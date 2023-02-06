import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.http import urlquote

from social.pipeline.social_auth import associate_by_email
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from social.exceptions import (AuthAlreadyAssociated,SocialAuthBaseException)
from social.utils import social_logger

ANONYMOUS_AVATAR = '/static/images/header/avatar.png'
(NO_AVATAR, GRAVATAR, TWITTER, FACEBOOK, PRIVATETAR) = (0, 1, 2, 3, 4)
AVATARS = (NO_AVATAR, GRAVATAR, TWITTER, FACEBOOK, PRIVATETAR)
logger = logging.getLogger(__name__)


def selectively_associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current auth with a user with the same email address in the DB.
    This pipeline entry is not 100% secure unless you know that the providers
    enabled enforce email verification on their side, otherwise a user can
    attempt to take over another user account by using the same (not validated)
    email address on some provider.  
    
    Not using Facebook or Twitter to authenticate a user.
    """
    if backend.name  in ('twitter', 'facebook'):
        return None
    return associate_by_email(backend, details, user=None, *args, **kwargs)

def facebook_extra_values( user,  extra_data):
    try:
        facebook_id = extra_data.get('id')
        user.profile.facebook_id = facebook_id
        if user.profile.avatar_source is None or user.profile.avatar_source is PRIVATETAR:
            user.profile.avatar_source = FACEBOOK
        user.profile.save()
        return True
    except Exception,e:
        logger.error(e)
        return False

def twitter_extra_values( user, extra_data):
    try:
        twitter_id = extra_data.get('screen_name')
        profile_image_url = extra_data.get('profile_image_url_https')
        user.profile.twitter_id = twitter_id
        if user.profile.avatar_source is None or user.profile.avatar_source in (TWITTER, PRIVATETAR):
            user.profile.pic_url = profile_image_url
        if user.profile.avatar_source is None or user.profile.avatar_source is PRIVATETAR:
            user.profile.avatar_source = TWITTER
        user.profile.save()
        return True
    except Exception,e:
        logger.error(e)
        return False
        
def deliver_extra_data(backend,  user, social, *args, **kwargs):
    if backend.name is 'twitter':
        twitter_extra_values( user, social.extra_data)
    if backend.name is 'facebook':
        facebook_extra_values( user, social.extra_data)

# following is needed because of length limitations in a unique constrain for MySQL
def chop_username(username, *args, **kwargs):
    if username and len(username)>222:
        return {'username':username[0:222]}

def selective_social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            if backend.name not in ('twitter', 'facebook'):
                msg = 'This {0} account is already in use.'.format(provider)
                raise AuthAlreadyAssociated(backend, msg)
        elif not user:
            user = social.user
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}

# https://stackoverflow.com/a/19361220
# adapting https://github.com/omab/python-social-auth/blob/v0.2.10/social/apps/django_app/middleware.py#L25

class SocialAuthExceptionMiddlewareWithoutMessages(SocialAuthExceptionMiddleware):
    """
    a modification of SocialAuthExceptionMiddleware to pass backend and message without
    attempting django.messages
    """ 
    def process_exception(self, request, exception):
    
        if isinstance(exception, SocialAuthBaseException):
            backend = getattr(request, 'backend', None)
            backend_name = getattr(backend, 'name', 'unknown-backend')

            message = self.get_message(request, exception)
            social_logger.error(message)

            url = self.get_redirect_uri(request, exception)
            url += ('?' in url and '&' or '?') + \
                   'message={0}&backend={1}'.format(urlquote(message),
                                                    backend_name)
            return redirect(url)
