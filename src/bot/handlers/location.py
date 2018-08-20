from bot.models import User


def handle_location(bot, telegram_message):
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
    user_id = telegram_message.from_user.id
    user = bot.get_storage(User).get(user_id)
    bot.evernote.create_note(
        user.evernote.access_token,
        user.evernote.notebook.guid,
        title='Location',
        html=html
    )
