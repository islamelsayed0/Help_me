"""
Stripe service for handling payment processing and subscriptions.
"""
import stripe
from django.conf import settings
from django.urls import reverse
from schoolgroups.models import SchoolGroup
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning('STRIPE_SECRET_KEY not configured. Stripe features will not work.')


def create_checkout_session(school_group, plan_type, request):
    """
    Create a Stripe Checkout Session for plan upgrade.
    
    Args:
        school_group: SchoolGroup instance
        plan_type: 'pro' or 'enterprise'
        request: Django request object
    
    Returns:
        Stripe Checkout Session object
    """
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('Stripe is not configured. Please set STRIPE_SECRET_KEY.')
    
    # Determine price ID based on plan
    price_id = None
    if plan_type == 'pro':
        # Default to monthly, can be extended to support yearly
        price_id = settings.STRIPE_PRICE_ID_PRO_MONTHLY
    elif plan_type == 'enterprise':
        price_id = settings.STRIPE_PRICE_ID_ENTERPRISE
    
    if not price_id:
        raise ValueError(f'Price ID not configured for plan: {plan_type}')
    
    # Build success and cancel URLs
    success_url = request.build_absolute_uri(reverse('accounts:stripe_checkout_success'))
    cancel_url = request.build_absolute_uri(reverse('accounts:subscription'))
    
    try:
        # Create or get Stripe customer
        customer_id = school_group.stripe_customer_id if hasattr(school_group, 'stripe_customer_id') else None
        
        if not customer_id:
            # Create new customer
            customer = stripe.Customer.create(
                email=request.user.email,
                name=school_group.name,
                metadata={
                    'school_group_id': school_group.id,
                    'user_id': request.user.id,
                }
            )
            customer_id = customer.id
            
            # Save customer ID to school group
            school_group.stripe_customer_id = customer_id
            school_group.save(update_fields=['stripe_customer_id'])
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'school_group_id': school_group.id,
                'plan_type': plan_type,
                'user_id': request.user.id,
            },
        )
        
        return session
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error creating checkout session: {str(e)}')
        raise


def create_ai_addon_subscription(school_group, request):
    """
    Create a Stripe subscription for AI Add-On ($7/month).
    
    Args:
        school_group: SchoolGroup instance
        request: Django request object
    
    Returns:
        Stripe Subscription object
    """
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('Stripe is not configured. Please set STRIPE_SECRET_KEY.')
    
    price_id = settings.STRIPE_PRICE_ID_AI_ADDON
    if not price_id:
        raise ValueError('AI Add-On price ID not configured.')
    
    try:
        # Get or create Stripe customer
        customer_id = school_group.stripe_customer_id if hasattr(school_group, 'stripe_customer_id') else None
        
        if not customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=school_group.name,
                metadata={
                    'school_group_id': school_group.id,
                    'user_id': request.user.id,
                }
            )
            customer_id = customer.id
            school_group.stripe_customer_id = customer_id
            school_group.save(update_fields=['stripe_customer_id'])
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{
                'price': price_id,
            }],
            metadata={
                'school_group_id': school_group.id,
                'subscription_type': 'ai_addon',
                'user_id': request.user.id,
            },
        )
        
        return subscription
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error creating AI addon subscription: {str(e)}')
        raise


def cancel_ai_addon_subscription(school_group):
    """
    Cancel the AI Add-On subscription.
    
    Args:
        school_group: SchoolGroup instance
    
    Returns:
        Stripe Subscription object (canceled)
    """
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('Stripe is not configured.')
    
    subscription_id = school_group.stripe_subscription_id if hasattr(school_group, 'stripe_subscription_id') else None
    if not subscription_id:
        raise ValueError('No active subscription found.')
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        canceled_subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return canceled_subscription
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error canceling subscription: {str(e)}')
        raise


def get_subscription_status(school_group):
    """
    Get current subscription status from Stripe.
    
    Args:
        school_group: SchoolGroup instance
    
    Returns:
        dict with subscription status information
    """
    if not settings.STRIPE_SECRET_KEY:
        return {'status': 'not_configured'}
    
    subscription_id = school_group.stripe_subscription_id if hasattr(school_group, 'stripe_subscription_id') else None
    if not subscription_id:
        return {'status': 'no_subscription'}
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
        }
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error retrieving subscription: {str(e)}')
        return {'status': 'error', 'error': str(e)}


def handle_webhook_event(event):
    """
    Handle a Stripe webhook event.
    
    Args:
        event: Stripe Event object
    
    Returns:
        bool: True if handled successfully
    """
    try:
        if event.type == 'checkout.session.completed':
            # Handle successful checkout
            session = event.data.object
            school_group_id = session.metadata.get('school_group_id')
            plan_type = session.metadata.get('plan_type')
            
            if school_group_id and plan_type:
                try:
                    school_group = SchoolGroup.objects.get(id=school_group_id)
                    school_group.plan = plan_type
                    school_group.stripe_customer_id = session.customer
                    if session.subscription:
                        school_group.stripe_subscription_id = session.subscription
                    school_group.save()
                    logger.info(f'Updated school group {school_group_id} to plan {plan_type}')
                except SchoolGroup.DoesNotExist:
                    logger.error(f'School group {school_group_id} not found')
        
        elif event.type == 'customer.subscription.updated':
            # Handle subscription update
            subscription = event.data.object
            customer_id = subscription.customer
            
            try:
                school_group = SchoolGroup.objects.get(stripe_customer_id=customer_id)
                school_group.stripe_subscription_id = subscription.id
                school_group.subscription_status = subscription.status
                
                # Update AI enabled status based on subscription
                if subscription.status == 'active':
                    # Check if this is an AI addon subscription
                    if subscription.metadata.get('subscription_type') == 'ai_addon':
                        school_group.ai_enabled = True
                        school_group.ai_plan = 'unlimited'
                elif subscription.status in ['canceled', 'unpaid', 'past_due']:
                    if subscription.metadata.get('subscription_type') == 'ai_addon':
                        school_group.ai_enabled = False
                        school_group.ai_plan = 'limited'
                
                school_group.save()
                logger.info(f'Updated subscription status for school group {school_group.id}')
            except SchoolGroup.DoesNotExist:
                logger.error(f'School group with customer {customer_id} not found')
        
        elif event.type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription = event.data.object
            customer_id = subscription.customer
            
            try:
                school_group = SchoolGroup.objects.get(stripe_customer_id=customer_id)
                if subscription.metadata.get('subscription_type') == 'ai_addon':
                    school_group.ai_enabled = False
                    school_group.ai_plan = 'limited'
                school_group.stripe_subscription_id = None
                school_group.subscription_status = 'canceled'
                school_group.save()
                logger.info(f'Canceled subscription for school group {school_group.id}')
            except SchoolGroup.DoesNotExist:
                logger.error(f'School group with customer {customer_id} not found')
        
        return True
    except Exception as e:
        logger.error(f'Error handling webhook event {event.type}: {str(e)}')
        return False
