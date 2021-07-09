from evernotebot.bot.shortcuts import get_message_caption


def on_location(bot, message: dict):
    latitude = message['location']['latitude']
    longitude = message['location']['longitude']
    maps_url = f'https://maps.google.com/maps?q={latitude},{longitude}'
    title = 'Location'
    html = f'<a href="{maps_url}">{maps_url}</a>'
    if venue := message.get('venue'):
        title = venue.get(title) or title
        address = venue['address']
        html = f'{title}<br />{address}<br /><a href="{maps_url}">{maps_url}</a>'
        if foursquare_id := venue.get('foursquare_id'):
            url = f'https://foursquare.com/v/{foursquare_id}'
            html += f'<br /><a href="{url}">{url}</a>'
    title = get_message_caption(message) or title
    bot.save_note(title=title, html=html)
