import time

from neomodel.exceptions import MultipleNodesReturned, DoesNotExist

from ..User import User

class LastfmUser(User):
    @classmethod
    def update_lastfm_tokens(cls, profile, token):
        try:
            user = cls.nodes.get(username=profile['username'])
        except MultipleNodesReturned:
            print(f"Multiple users found with username: {profile['username']}")
            return None
        except DoesNotExist:
            user = cls.create_from_lastfm_profile(profile, token)
        user.access_token = token
        user.token_issue_time = str(time.time())
        user.is_active = True
        user.save()
        return user

    @classmethod
    def create_from_lastfm_profile(cls, profile, token):
        user_data = {
            'username': profile['username'],
            'access_token': token,
        }
        user = cls(**user_data)
        user.save()
        return user
