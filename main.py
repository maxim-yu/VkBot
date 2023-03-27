import vk_app_module as app
import vk_bot_module as bot
import os_module as osm
import db_module as db
from vk_api.longpoll import VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def forward_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('вперед', color=VkKeyboardColor.NEGATIVE)
    return keyboard


def next_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_openlink_button(f'{vk_user_name} &#127380;', link=f'https://vk.com/id{vk_user_id}')
    keyboard.add_button("вперед", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('все команды', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('добавить в ЧС', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('в избранное', color=VkKeyboardColor.POSITIVE)
    return keyboard


def hello_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('быстрый поиск', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('продолжить последний поиск', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('очистить просмотры и избранное', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('просмотреть избранное', color=VkKeyboardColor.POSITIVE)
    return keyboard


def get_vk_users_like_my_user():
    my_id = bot_connection.get_user(event.user_id)
    my_user_data = bot_connection.find_my_user_params(event.user_id, my_id)
    search_model_params = bot.get_search_params_data(my_user_data)
    users_list = app_connection.quick_search_for_online_users(search_model_params)
    return users_list


def del_viewed_users(all_ids):
    temp_data = list()
    have_seen_list = db.get_all_ids_in_table()
    for item in all_ids:
        if item[0] not in have_seen_list:
            temp_data.append(item)
    return temp_data


def upload_img_msg(files):
    osm.go_into_temp_dir()
    for photo in files:
        upload_image = bot_connection.photo_loading.photo_messages(photos=photo)[0]
        attachments = f"photo{upload_image['owner_id']}_{upload_image['id']}"
        link_data = app_connection.get_links_for_like_and_cancel_like(vk_user_id)
        like_link = link_data['like']
        cancel_like_link = link_data['dislike']
        keyboard = VkKeyboard(inline=True)
        keyboard.add_openlink_button('&#10084;', link=like_link + (photo.split('.')[0]))
        keyboard.add_openlink_button('&#128148;', link=cancel_like_link + (photo.split('.')[0]))
        bot_connection.write_keyboard_message(event.user_id, None, keyboard, attachments)
    osm.go_back_into_work_dir()


if __name__ == '__main__':
    osm.create_temp_dir_if_not_exists()
    app_connection = app.VKApp()
    bot_connection = bot.VkBot()
    user_ids_and_names = []
    vk_user_id = int()

    for event in bot_connection.long_polling.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text

            if request in  ['привет', 'start', 'старт', 'hi', 'hello', 'privet', 'хай', 'салют', 'здрасте']:
                hello_message = 'Привет &#128075;\nЯ умею подбирать пары пользователям во Вконтакте.\nВыбери действие.'
                keyboard = hello_keyboard()
                bot_connection.write_keyboard_message(event.user_id, hello_message, keyboard)

            elif request == "быстрый поиск":
                db.clear_unviewed_ids()
                all_user_ids_and_names = get_vk_users_like_my_user()
                user_ids_and_names = del_viewed_users(all_user_ids_and_names)
                db.fill_data_in_db(user_ids_and_names)
                keyboard = forward_keyboard()
                search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
                bot_connection.write_keyboard_message(event.user_id, search_msg, keyboard)

            elif request == "вперед":
                if len(user_ids_and_names) > 0:
                    some_data = user_ids_and_names.pop()
                    vk_user_id = some_data[0]
                    vk_user_name = some_data[1]
                    popular_photo_list = app_connection.get_popular_user_photos(vk_user_id)
                    bot_connection.write_message(event.user_id, f'{vk_user_name}\nhttps://vk.com/id{vk_user_id}')
                    files_in_directory = osm.download_photo_in_temp_dir(popular_photo_list)
                    upload_img_msg(files_in_directory)
                    next_message = f"Впереди еще {len(user_ids_and_names)} &#127380;"
                    keyboard = next_keyboard()
                    bot_connection.write_keyboard_message(event.user_id, next_message, keyboard)
                    osm.remove_temporary_files()
                    db.mark_as_viewed(vk_user_id)

                else:
                    keyboard = hello_keyboard()
                    bot_connection.write_keyboard_message(event.user_id, 'Список пользователей пуст', keyboard)

            elif request == "продолжить последний поиск":
                user_ids_and_names = db.get_unviewed_ids()
                search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
                keyboard = forward_keyboard()
                bot_connection.write_keyboard_message(event.user_id, search_msg, keyboard)

            elif request == "просмотреть избранное":
                user_ids_and_names = db.get_favorite_ids()
                search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
                keyboard = forward_keyboard()
                bot_connection.write_keyboard_message(event.user_id, search_msg, keyboard)

            elif request == "в избранное":
                db.mark_as_favourite(vk_user_id)
                bot_connection.write_message(event.user_id, f'id{vk_user_id} добавлен в избранное.')

            elif request == "добавить в ЧС":
                db.mark_as_blacklisted(vk_user_id)
                bot_connection.write_message(event.user_id, f'id{vk_user_id} добавлен в ЧС.')

            elif request == "очистить просмотры и избранное":
                db.clear_history_and_favorite()
                remove_msg = 'Просмотры и избранное очищены, ЧС сохранен.'
                keyboard = hello_keyboard()
                bot_connection.write_keyboard_message(event.user_id, remove_msg, keyboard)

            elif request == "все команды":
                msg = "Что мне сделать?"
                keyboard = hello_keyboard()
                bot_connection.write_keyboard_message(event.user_id, msg, keyboard)

            else:
                msg = "Не известная команда!"
                keyboard = hello_keyboard()
                bot_connection.write_keyboard_message(event.user_id, msg, keyboard)
