from authorization_data import vk_bot_token
from vk_api import VkUpload, VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from random import randrange
from datetime import datetime
import vk_app_module as app


class VkBot:
    def __init__(self):
        self.token = vk_bot_token
        self.vk_bot = VkApi(token=self.token)
        self.long_polling = VkLongPoll(self.vk_bot)
        self.photo_loading = VkUpload(self.vk_bot)

    def write_message(self, user_id, message, attachments=None):
        self.vk_bot.method('messages.send', {'user_id': user_id,
                                             'message': message,
                                             'attachment': attachments,
                                             'random_id': randrange(10 ** 7), })

    def write_keyboard_message(self, user_id, message, keyboard, attachments=None):
        self.vk_bot.method('messages.send', {'user_id': user_id,
                                             'message': message,
                                             'keyboard': keyboard.get_keyboard(),
                                             'attachment': attachments,
                                             'random_id': randrange(10 ** 7), })

    def get_user(self, user_id) -> int:
        self.write_message(user_id, 'Введите id пользователя ВКонтакте для которого будем искать пару.')
        for event in self.long_polling.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    my_user = int(event.text)
                    return my_user
                except ValueError:
                    return self.get_user(user_id)

    def find_my_user_params(self, event_id, my_id) -> dict:
        data_params = {'user_ids': my_id,
                       'fields': 'bdate,country,city,sex'}
        data = self.vk_bot.method('users.get', {**data_params})
        my_user_params = {}
        for info in data:
            if 'country' in info:
                my_user_params['country'] = info['country']['id']
            else:
                my_user_params['country'] = self.set_country(event_id)

            if 'city' in info:
                my_user_params['city'] = info['city']['id']
            else:
                my_user_params['city'] = self.set_city(event_id)

            if 'sex' in info:
                my_user_params['sex'] = info['sex']
            else:
                my_user_params['sex'] = self.set_sex(event_id)

            if 'bdate' in info and len(info['bdate'].split('.')) == 3:
                my_user_params['age'] = calculate_age(info['bdate'])
            else:
                my_user_params['age'] = self.set_age(event_id)
        return my_user_params

    def set_country(self, event_user_id) -> int:
        self.write_message(event_user_id, "Введите страну поиска как в примере: RU,UA,BY...")
        for event in self.long_polling.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                country_id = event.text
                app_connection = app.VKApp()
                result = app_connection.find_country_id(country_id)
                if result:
                    return result
                else:
                    return self.set_country(event_user_id)

    def set_city(self, event_user_id) -> int:
        self.write_message(event_user_id, "Введите город заданного пользователя.")
        for event in self.long_polling.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                city_in_text = event.text
                app_connection = app.VKApp()
                result = app_connection.find_city_id(city_in_text)
                if result:
                    return result
                else:
                    return self.set_city(event_user_id)

    def set_sex(self, event_user_id) -> int:
        self.write_message(event_user_id, "Введите пол заданного пользователя:\n1 - Женский\n2 - Мужской")
        for event in self.long_polling.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text in [1, 2, '1', '2']:
                    sex = int(event.text)
                    return sex
                else:
                    return self.set_sex(event_user_id)

    def set_age(self, event_user_id) -> int:
        self.write_message(event_user_id, "Введите возраст заданного пользователя.")
        for event in self.long_polling.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    age = int(event.text)
                    return age
                except ValueError:
                    return self.set_age(event_user_id)


def get_search_params_data(user_data) -> dict:
    age_range = 3

    if user_data['sex'] == 1:
        sex = 2
    else:
        sex = 1

    search_data = {
        'country': user_data['country'],
        'city': user_data['city'],
        'age_from': user_data['age'] - age_range,
        'age_to': user_data['age'] + age_range,
        'sex': sex
    }
    return search_data


def calculate_age(day_of_birth) -> int:
    sample = ["day", "month", "year"]
    instance = list(map(int, day_of_birth.split('.')))
    birthday_data = dict(zip(sample, instance))
    right_now = datetime.now()
    birth_date = datetime(birthday_data['year'], birthday_data['month'], birthday_data['day'])
    return int((right_now - birth_date).days / 365)
