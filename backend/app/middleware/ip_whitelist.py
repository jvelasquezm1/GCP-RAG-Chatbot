"""IP whitelisting middleware for ingestion endpoints."""
from fastapi import Request, HTTPException, status
from typing import List
import ipaddress
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Handles various proxy headers (X-Forwarded-For, X-Real-IP) that are
    commonly used by load balancers and reverse proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address as string
    """
    # Check X-Forwarded-For header (most common for proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        client_ip = forwarded_for.split(",")[0].strip()
        logger.debug(f"Extracted IP from X-Forwarded-For: {client_ip}")
        return client_ip
    
    # Check X-Real-IP header (alternative proxy header)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        logger.debug(f"Extracted IP from X-Real-IP: {real_ip}")
        return real_ip.strip()
    
    # Fallback to direct client IP
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"Using direct client IP: {client_ip}")
    return client_ip


def is_ip_whitelisted(ip: str, whitelist: List[str]) -> bool:
    """
    Check if an IP address is in the whitelist.
    
    Supports both individual IPs and CIDR ranges.
    
    Args:
        ip: IP address to check
        whitelist: List of whitelisted IPs or CIDR ranges
        
    Returns:
        True if IP is whitelisted, False otherwise
    """
    if not whitelist:
        # Empty whitelist means all IPs are allowed (not recommended for production)
        logger.warning("IP whitelist is empty - allowing all IPs")
        return True
    
    try:
        client_ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        return False
    
    for whitelisted in whitelist:
        try:
            # Try as CIDR range first
            if "/" in whitelisted:
                network = ipaddress.ip_network(whitelisted, strict=False)
                if client_ip_obj in network:
                    logger.info(f"IP {ip} matched CIDR range {whitelisted}")
                    return True
            else:
                # Try as individual IP
                whitelisted_ip = ipaddress.ip_address(whitelisted)
                if client_ip_obj == whitelisted_ip:
                    logger.info(f"IP {ip} matched whitelisted IP {whitelisted}")
                    return True
        except ValueError:
            logger.warning(f"Invalid whitelist entry: {whitelisted}")
            continue
    
    return False


async def ip_whitelist_middleware(request: Request, call_next):
    """
    Middleware to check IP whitelist for ingestion endpoints.
    
    Only applies to /ingest endpoints. Other endpoints are not affected.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        Response from next handler
        
    Raises:
        HTTPException: If IP is not whitelisted and endpoint requires it
    """
    # Only check whitelist for ingestion endpoints
    if request.url.path.startswith("/ingest"):
        if not settings.ingestion_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document ingestion is currently disabled"
            )
        
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Check whitelist
        whitelist = settings.get_ip_whitelist()
        if whitelist:
            if not is_ip_whitelisted(client_ip, whitelist):
                logger.warning(
                    f"IP {client_ip} attempted to access ingestion endpoint "
                    f"but is not whitelisted"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Your IP address is not whitelisted."
                )
            else:
                logger.info(f"IP {client_ip} is whitelisted, allowing access")
    
    # Continue to next handler
    response = await call_next(request)
    return response
