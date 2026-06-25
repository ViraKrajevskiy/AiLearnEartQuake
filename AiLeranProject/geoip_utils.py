import requests
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Gets the client's real IP address, accounting for proxies and load balancers
    """
    # Check X-Forwarded-For (cloud services, nginx)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Check CF-Connecting-IP (Cloudflare)
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip

    # Check X-Real-IP (common proxy header)
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip

    # Fallback to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_country_by_ip(ip_address):
    """
    Determines country by IP address using ip-api.com (free API)
    Uses cache to save API requests

    Returns: {'country': str, 'country_code': str, 'city': str} or None on error
    """
    # Skip private/local IPs
    if not ip_address:
        return None

    # Check for private IP ranges
    private_prefixes = ('127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                        '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                        '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '0.0.0.0')

    if ip_address.startswith(private_prefixes) or ip_address == '0.0.0.0':
        return None

    # Check cache (5 minutes)
    cache_key = f'geoip_{ip_address}'
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"GeoIP cache hit for {ip_address}")
        return cached

    try:
        # ip-api.com is free with 45 requests per minute limit
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3,
            params={'fields': 'status,country,countryCode,city,isp,regionName'}
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'success':
                result = {
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', '').upper(),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                }

                # Cache result for 5 minutes
                cache.set(cache_key, result, 300)
                logger.debug(f"GeoIP: {ip_address} → {result['country']}")
                return result
            else:
                logger.warning(f"GeoIP API returned error for {ip_address}: {data}")

        logger.warning(f"GeoIP API error for {ip_address}: {response.status_code}")
        return None

    except requests.Timeout:
        logger.warning(f"GeoIP API timeout for {ip_address}")
        return None
    except requests.RequestException as e:
        logger.error(f"GeoIP request error for {ip_address}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"GeoIP error for {ip_address}: {str(e)}")
        return None