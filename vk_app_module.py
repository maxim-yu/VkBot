from authorization_data import vk_app_token
from datetime import datetime
from vk_api import VkApi


class VKApp:
    def __init__(self, version='5.131'):
        self.token = vk_app_token
        self.app_connection = VkApi(token=self.token)
        self.version = version

    def get_links_for_like_and_cancel_like(self, owner_id) -> dict:
        links_data = dict()
        links_data['like'] = self.create_like_link(owner_id)
        links_data['dislike'] = self.create_cancel_like_link(owner_id)
        return links_data

    def create_like_link(self, owner_id) -> str:
        half_link = f'https://api.vk.com/method/likes.add?' \
            f'access_token={self.token}&v={self.version}&owner_id={owner_id}&type=photo&item_id='
        return half_link

    def create_cancel_like_link(self, owner_id) -> str:
        half_link = f'https://api.vk.com/method/likes.delete?' \
            f'access_token={self.token}&v={self.version}&owner_id={owner_id}&type=photo&item_id='
        return half_link

    def find_city_id(self, city) -> int:
        params = {'q': city, 'count': 1}
        city_data = self.app_connection.method('database.getCities', {**params})
        city_items = city_data['items']
        if len(city_items) == 0:
            return False
        for line in city_items:
            city_id = line['id']
            return int(city_id)

    def find_country_id(self, country) -> int:
        params = {'code': country, 'count': 1}
        country_data = self.app_connection.method('database.getCountries', {**params})
        for case in country_data['items']:
            return int(case['id'])

    def get_photos_data(self, vk_user_id) -> dict:
        data_params = {'owner_id': vk_user_id, 'album_id': 'profile', 'extended': 1}
        photos_data = self.app_connection.method('photos.get', {**data_params})
        return photos_data

    def get_popular_user_photos(self, owner_id) -> list:
        popular_photos_data = {}
        photo_data = self.get_photos_data(owner_id)

        for info in photo_data['items']:
            photo_link = (info['sizes'][-1]['url'], info['id'])
            value_of_popularity = info['likes']['count'] + info['comments']['count']
            popular_photos_data[photo_link] = value_of_popularity
        if len(popular_photos_data) <= 3:
            most_popular_photos = list(popular_photos_data.keys())
        else:
            x_photos_data = (sorted(popular_photos_data.items(), key=lambda popular: popular[1])[::-1])[0:3]
            most_popular_photos = [url[0] for url in x_photos_data]
        return most_popular_photos

    def quick_search_for_online_users(self, data_params) -> list:
        params = {
            'count': 1000,
            'fields': 'country,city,relation',
            'city': data_params['city'],
            'country': data_params['country'],
            'sex': data_params['sex'],
            'age_from': data_params['age_from'],
            'age_to': data_params['age_to'],
            'has_photo': 1,
            'online': 1
        }
        users_list = []
        response = self.app_connection.method('users.search', {**params})
        for item in response['items']:
            if item['is_closed'] == 0:
                try:
                    if item['city']['id'] == data_params['city'] and item['relation'] in [1, 6]:
                        users_list.append([item['id'], f"{item['first_name']} {item['last_name']}"])
                except KeyError:
                    pass
        return users_list


def check_last_visit(time_stamp) -> bool:
    x_days = 86400 * 30
    right_now = datetime.now()
    right_now_stamp = int(datetime.timestamp(right_now))
    if right_now_stamp - time_stamp > x_days:
        return False
    return True
