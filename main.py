import vk_app_module as app
import vk_bot_module as bot
from vk_api.longpoll import VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os_module as osm
import db_module as db

osm.create_temp_dir_if_not_exists()

app_connection = app.VKApp()
bot_connection = bot.VkBot()
user_ids_and_names = []
vk_user_id = int()

for event in bot_connection.long_polling.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text
        if request == 'привет':
            hello_message = 'Привет &#128075;\nЯ умею подбирать пары пользователям во Вконтакте.\nВыбери действие.'
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button('новый поиск', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('продолжить последний поиск', color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button('очистить просмотры и избранное', color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button('просмотреть избранное', color=VkKeyboardColor.POSITIVE)
            bot_connection.write_keyboard_message(event.user_id, hello_message, keyboard)

        elif request == "новый поиск":
            db.clear_unviewed_ids()

            my_user_id = bot_connection.get_user(event.user_id)
            my_user_data = bot_connection.find_my_user_params(event.user_id, my_user_id)
            search_model_params = bot.get_search_params_data(my_user_data)
            user_ids_and_names = app_connection.quick_search_for_online_users(search_model_params)
            temp_data = list()
            have_seen_list = db.get_all_ids_in_table()
            for item in user_ids_and_names:
                if item[0] not in have_seen_list:
                    temp_data.append(item)
            user_ids_and_names = temp_data
            db.fill_data_in_db(user_ids_and_names)

            search_keyboard = VkKeyboard(one_time=False)
            search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
            search_keyboard.add_button('вперед', color=VkKeyboardColor.NEGATIVE)
            bot_connection.write_keyboard_message(event.user_id, search_msg, search_keyboard)

        elif request == "вперед":
            if len(user_ids_and_names) > 0:
                some_data = user_ids_and_names.pop()
                vk_user_id = some_data[0]
                vk_user_name = some_data[1]

                popular_photo_list = app_connection.get_popular_user_photos(vk_user_id)
                bot_connection.write_message(event.user_id, f'{vk_user_name}\nhttps://vk.com/id{vk_user_id}')
                files_in_directory = osm.download_photo_in_temp_dir(popular_photo_list)

                osm.go_into_temp_dir()

                for photo in files_in_directory:
                    upload_image = bot_connection.photo_loading.photo_messages(photos=photo)[0]
                    attachments = f"photo{upload_image['owner_id']}_{upload_image['id']}"

                    link_data = app_connection.get_links_for_like_and_cancel_like(vk_user_id)
                    like_link = link_data['like']
                    cancel_like_link = link_data['dislike']

                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_openlink_button('&#10084;', link=like_link+(photo.split('.')[0]))
                    keyboard.add_openlink_button('&#128148;', link=cancel_like_link+(photo.split('.')[0]))
                    bot_connection.write_keyboard_message(event.user_id, None, keyboard, attachments)

                osm.go_back_into_work_dir()

                keyboard_next = VkKeyboard(one_time=False)
                next_message = f"Впереди еще {len(user_ids_and_names)} &#127380;"
                keyboard_next.add_openlink_button(f'{vk_user_name} &#127380;', link=f'https://vk.com/id{vk_user_id}')
                keyboard_next.add_button("вперед", color=VkKeyboardColor.NEGATIVE)
                keyboard_next.add_line()
                keyboard_next.add_button('добавить в черный список', color=VkKeyboardColor.POSITIVE)
                keyboard_next.add_button('добавить в избранное', color=VkKeyboardColor.POSITIVE)
                bot_connection.write_keyboard_message(event.user_id, next_message, keyboard_next)
                osm.remove_temporary_files()
                db.mark_as_viewed(vk_user_id)
            else:
                keyboard_st = VkKeyboard()
                keyboard_st.add_button("новый поиск", color=VkKeyboardColor.POSITIVE)
                keyboard_st.add_button("очистить просмотры и избранное", color=VkKeyboardColor.POSITIVE)
                bot_connection.write_keyboard_message(event.user_id, 'Список пользователей пуст', keyboard_st)

        elif request == "продолжить последний поиск":
            user_ids_and_names = db.get_unviewed_ids()
            last_search_keyboard = VkKeyboard(one_time=True)
            search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
            last_search_keyboard.add_button('вперед', color=VkKeyboardColor.NEGATIVE)
            bot_connection.write_keyboard_message(event.user_id, search_msg, last_search_keyboard)

        elif request == "просмотреть избранное":
            user_ids_and_names = db.get_favorite_ids()
            last_search_keyboard = VkKeyboard(one_time=True)
            search_msg = f"Количество подходящих страниц: {len(user_ids_and_names)}\nЖми 'вперед' для просмотра "
            last_search_keyboard.add_button('вперед', color=VkKeyboardColor.NEGATIVE)
            bot_connection.write_keyboard_message(event.user_id, search_msg, last_search_keyboard)

        elif request == "добавить в избранное":
            db.mark_as_favourite(vk_user_id)

        elif request == "добавить в черный список":
            db.mark_as_blacklisted(vk_user_id)

        elif request == "очистить просмотры и избранное":
            db.clear_history_and_favorite()

        else:
            bot_connection.write_message(event.user_id, "Не известная команда!")
