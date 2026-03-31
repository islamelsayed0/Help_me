"""
Stripe webhook handler: signature verification, idempotency, server-side only.
"""
import logging
from datetime import datetime, timezone as datetime_timezone

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """
    Accept only POST. Verify Stripe-Signature using STRIPE_WEBHOOK_SECRET.
    Idempotent: each event id is processed at most once.
    """
    secret = (getattr(settings, 'STRIPE_WEBHOOK_SECRET', None) or '').strip()
    if not secret:
        logger.error('Stripe webhook called but STRIPE_WEBHOOK_SECRET is not configured')
        return HttpResponse(status=503)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        logger.warning('Stripe webhook: invalid payload')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning('Stripe webhook: invalid signature')
        return HttpResponse(status=400)

    event_id = event.get('id')
    event_type = event.get('type', '')
    if not event_id:
        return HttpResponse(status=400)

    from schoolgroups.models import StripeWebhookEvent, SchoolGroup

    try:
        with transaction.atomic():
            record = (
                StripeWebhookEvent.objects.select_for_update()
                .filter(stripe_event_id=event_id)
                .first()
            )
            if record and record.processed_at:
                return HttpResponse(status=200)
            if record is None:
                try:
                    record = StripeWebhookEvent.objects.create(
                        stripe_event_id=event_id,
                        event_type=event_type[:255],
                    )
                except IntegrityError:
                    record = StripeWebhookEvent.objects.select_for_update().get(
                        stripe_event_id=event_id
                    )
            if record.processed_at:
                return HttpResponse(status=200)
            _dispatch_event(event, SchoolGroup)
            record.processed_at = timezone.now()
            record.save(update_fields=['processed_at'])
    except Exception:
        logger.exception('Stripe webhook handler failed for event %s', event_id)
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def _dispatch_event(event, SchoolGroup):
    """Apply supported Stripe events (subscription / customer linkage)."""
    etype = event.get('type')
    obj = event.get('data', {}).get('object') or {}

    if etype == 'checkout.session.completed':
        meta = obj.get('metadata') or {}
        sg_id = meta.get('school_group_id')
        customer_id = obj.get('customer')
        sub_id = obj.get('subscription')
        if sg_id and customer_id:
            try:
                group = SchoolGroup.objects.get(pk=int(sg_id))
            except (ValueError, SchoolGroup.DoesNotExist):
                logger.warning('checkout.session.completed: invalid school_group_id=%s', sg_id)
                return
            updates = {'stripe_customer_id': customer_id}
            if sub_id:
                updates['stripe_subscription_id'] = sub_id
            SchoolGroup.objects.filter(pk=group.pk).update(**updates)

    elif etype == 'customer.subscription.updated':
        customer_id = obj.get('customer')
        sub_id = obj.get('id')
        status = obj.get('status', '') or ''
        if not customer_id:
            return
        period_end = obj.get('current_period_end')
        period_end_dt = None
        if period_end:
            period_end_dt = datetime.fromtimestamp(period_end, tz=datetime_timezone.utc)
        SchoolGroup.objects.filter(stripe_customer_id=customer_id).update(
            stripe_subscription_id=sub_id,
            subscription_status=status,
            subscription_current_period_end=period_end_dt,
        )

    elif etype == 'customer.subscription.deleted':
        customer_id = obj.get('customer')
        status = obj.get('status', '') or 'canceled'
        if not customer_id:
            return
        SchoolGroup.objects.filter(stripe_customer_id=customer_id).update(
            stripe_subscription_id=None,
            subscription_status=status,
        )
