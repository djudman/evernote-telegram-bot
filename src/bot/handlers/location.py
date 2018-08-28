from bot.models import User


def handle_location(bot, telegram_message):
    status_message = bot.api.sendMessage(telegram_message.chat.id, 'Location accepted')
    latitude = telegram_message.location.latitude
    longitude = telegram_message.location.longitude
    maps_url = "https://maps.google.com/maps?q=%(lat)f,%(lng)f" % {
        'lat': latitude,
        'lng': longitude,
    }
    title = 'Location'
    html = "<a href='{url}'>{url}</a>".format(url=maps_url)
    if telegram_message.venue:
        venue = telegram_message.venue
        html = "{title}<br />{address}<br /><a href='{url}'>{url}</a>".format(
            title=venue.title or title,
            address=venue.address,
            url=maps_url
        )
        foursquare_id = venue.foursquare_id
        if foursquare_id:
            url = 'https://foursquare.com/v/{}'.format(foursquare_id)
            html += "<br /><a href='{url}'>{url}</a>".format(url=url)
    user = bot.get_user(telegram_message)
    bot.save_note(user, title='Location', html=html)
    bot.api.editMessageText(telegram_message.chat.id, status_message['message_id'], 'Saved')
