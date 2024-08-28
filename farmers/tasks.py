###tasks.py
from celery import shared_task
from .scraper import process_and_scrape_data
from .models import *  
import requests
from django.core.files.base import ContentFile
import logging
from django.core.files import File
from tempfile import NamedTemporaryFile
from django.conf import settings
import os
from datetime import datetime
logger = logging.getLogger('farmers')
@shared_task
def process_and_scrape_data_task():
    try:
        posts = process_and_scrape_data()
        current_date = datetime.now().date()
        excluded_images = [
            'https://kisansamadhan.com/wp-content/uploads/2023/06/kisan-samadhan-logo-head.webp',
            'https://akm-img-a-in.tosshub.com/lingo/ktak/resources/img/default-ktak.png?size=216:121',
            'https://secure.gravatar.com/avatar/1b22ba0618fdd77bbeece05657e46c52?s=25&d=https%3A%2F%2Fkisansamadhan.com%2Fwp-content%2Fuploads%2F2023%2F09%2Fkisan-samadhan-logo-150x150.webp&r=g',
            'https://cdn.abplive.com/imagebank/default_16x9.png'
        ]

        for article_data in posts:
            article_data['image'] = [img for img in article_data['image'] if img not in excluded_images]

            title = article_data.get('title', 'No Title')
            content = article_data.get('content', 'No Content')
            url = article_data.get('url', '')
            source = article_data.get('source', 'Unknown')
            images = article_data.get('image', [])
            related_post = article_data.get('data_type', 'Additional Info')
            language_code = article_data.get('language')

            language_obj, created = LanguageSelection.objects.get_or_create(language=language_code)

            existing_articles = CurrentNews.objects.filter(
                title=title,
                content=content,
                link=url,
                source=source,
                related_post=related_post,
                fk_language=language_obj
            )

            if existing_articles.exists():
                article = existing_articles.first()
                article.created_at = current_date
            else:
                article = CurrentNews(
                    title=title,
                    content=content,
                    link=url,
                    source=source,
                    related_post=related_post,
                    fk_language=language_obj,
                    created_at=current_date
                )

            # Save the first image (if available)
            if images:
                img_url = images[0]
                try:
                    response = requests.get(img_url)
                    response.raise_for_status()
                    if response.headers['Content-Type'].startswith('image/'):
                        img_filename = f"{article.id}_{title[:30]}.jpg"
                        img_path = f'article_images/{img_filename}'

                        img_temp = NamedTemporaryFile(delete=True)
                        img_temp.write(response.content)
                        img_temp.flush()

                        article.image.save(img_path, File(img_temp), save=True)
                    else:
                        logger.warning(f"Skipping non-image URL: {img_url}")
                except requests.RequestException as e:
                    logger.error(f"Error downloading image from {img_url}: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error when handling image {img_url}: {str(e)}")

            article.save()

        return "Data scraped and saved successfully"
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return f"An error occurred: {str(e)}"
    
@shared_task
def backup_database():
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backup_file = os.path.join(backup_dir, 'daily_backup.sql')
    os.makedirs(backup_dir, exist_ok=True)
    db_password = os.getenv('DB_PASSWORD')  
    db_user = os.getenv('DB_USER')
    os.system(f'mysqldump -u {db_user} -p{db_password} agrisarthi > {backup_file}')


########--------------------------------------------Fruits Pop Stage Completion------------------------------##############