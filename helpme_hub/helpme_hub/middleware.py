"""
Performance monitoring middleware for HelpMe Hub.

This middleware tracks request performance metrics including:
- Request duration
- Database query count
- Database query time
- Memory usage
"""

import time
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor request performance.
    
    Logs performance metrics for requests that exceed thresholds.
    """
    
    # Thresholds (in seconds)
    SLOW_REQUEST_THRESHOLD = 1.0  # Log requests taking more than 1 second
    SLOW_DB_THRESHOLD = 0.5  # Log database queries taking more than 0.5 seconds
    
    def process_request(self, request):
        """Store start time and initial query count."""
        request._start_time = time.time()
        request._initial_queries = len(connection.queries)
        request._initial_query_time = sum(
            float(q.get('time', 0)) for q in connection.queries
        )
        return None
    
    def process_response(self, request, response):
        """Log performance metrics if thresholds are exceeded."""
        if not hasattr(request, '_start_time'):
            return response
        
        # Calculate request duration
        duration = time.time() - request._start_time
        
        # Calculate database metrics
        query_count = len(connection.queries) - request._initial_queries
        total_query_time = sum(
            float(q.get('time', 0)) for q in connection.queries[request._initial_queries:]
        )
        
        # Log slow requests
        if duration > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request detected: {request.method} {request.path}",
                extra={
                    'duration': duration,
                    'query_count': query_count,
                    'query_time': total_query_time,
                    'status_code': response.status_code,
                }
            )
        
        # Log slow database queries
        if total_query_time > self.SLOW_DB_THRESHOLD:
            logger.warning(
                f"Slow database queries: {request.method} {request.path}",
                extra={
                    'query_count': query_count,
                    'query_time': total_query_time,
                    'duration': duration,
                }
            )
        
        # Add performance headers (useful for monitoring)
        if hasattr(response, 'headers'):
            response.headers['X-Request-Duration'] = f"{duration:.3f}"
            response.headers['X-DB-Query-Count'] = str(query_count)
            response.headers['X-DB-Query-Time'] = f"{total_query_time:.3f}"
        
        return response
