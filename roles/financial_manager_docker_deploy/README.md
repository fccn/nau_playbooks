# financial_manager docker deploy

After deployment you need to create an user and an access token.

Example:
```bash
python manage.py createsuperuser --noinput --username openedx_ecommerce --email alertas@nau.edu.pt

python manage.py drf_create_token openedx_ecommerce
```

And some normal users that will manage the application using the Django Admin.
```bash
python manage.py createsuperuser --noinput --username <username> --email <email@fccn.pt>
```
