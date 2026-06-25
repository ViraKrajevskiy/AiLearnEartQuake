import requests
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Получает реальный IP адрес клиента, учитывая proxies и load balancers
    """
    # Сначала проверяем X-Forwarded-For (облачные сервисы, nginx)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Затем CF-Connecting-IP (Cloudflare)
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip

    # В противном случае используем REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_country_by_ip(ip_address):
    """
    Определяет страну по IP адресу используя ip-api.com (бесплатный API)
    Использует кеш для экономии на API запросах
    
    Returns: {'country': str, 'country_code': str, 'city': str} или None если ошибка
    """
    
    if not ip_address or ip_address == '0.0.0.0':
        return None

    # Проверяем кеш (5 минут)
    cache_key = f'geoip_{ip_address}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # ip-api.com бесплатный, но с лимитом 45 запросов в минуту
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3,
            params={'fields': 'status,country,countryCode,city,isp'}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                result = {
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', '').upper(),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                }
                
                # Кешируем результат на 5 минут
                cache.set(cache_key, result, 300)
                return result
        
        logger.warning(f"GeoIP API error for {ip_address}: {response.status_code}")
        return None
        
    except requests.Timeout:
        logger.warning(f"GeoIP API timeout for {ip_address}")
        return None
    except Exception as e:
        logger.error(f"GeoIP error for {ip_address}: {str(e)}")
        return None


def get_country_by_ip_maxmind(ip_address):
    # from geoip2.database import Reader
    # import geoip2.errors
    #
    # try:
    #     reader = Reader('GeoLite2-Country.mmdb')  # Путь к БД файлу
    #     response = reader.country(ip_address)
    #     return {
    #         'country': response.country.name,
    #         'country_code': response.country.iso_code,
    #     }
    # except geoip2.errors.AddressNotFoundError:
    #     logger.warning(f"IP {ip_address} not found in MaxMind DB")
    #     return None
    # except Exception as e:
    #     logger.error(f"MaxMind error: {e}")
    #     return None
    pass
