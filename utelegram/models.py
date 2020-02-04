from dataclasses import dataclass, asdict
from typing import List


def init_dataclass_fields(obj):
    def init_field_value(value, field_type):
        if value is None:
            return
        if hasattr(field_type, '_name') and field_type._name == 'List':
            value_type = field_type.__args__[0]
            return [init_field_value(v, value_type) for v in value]
        elif hasattr(field_type, '__dataclass_fields__'):
            return field_type(**value)
        return value

    for name, field in obj.__dataclass_fields__.items():
        value = getattr(obj, name)
        new_value = init_field_value(value, field.type)
        setattr(obj, name, new_value)


@dataclass(frozen=True)
class ChatPhoto:
    small_file_id: str  # Unique file identifier of small (160x160) chat photo.
                        # This file_id can be used only for photo download.
    big_file_id: str  # Unique file identifier of big (640x640) chat photo.
                      # This file_id can be used only for photo download.


@dataclass(frozen=True)
class MaskPosition:
    '''
    This object describes the position on faces where a mask should be placed
    by default.
    '''
    point: str  # The part of the face relative to which the mask should be
                # placed. One of “forehead”, “eyes”, “mouth”, or “chin”.
    x_shift: float  # Shift by X-axis measured in widths of the mask scaled
                    # to the face size, from left to right. For example,
                    # choosing -1.0 will place mask just to the left of
                    # the default mask position.
    y_shift: float  # Shift by Y-axis measured in heights of the mask
                    # scaled to the face size, from top to bottom.
                    # For example, 1.0 will place the mask just below
                    # the default mask position.
    scale: float  # Mask scaling coefficient. For example, 2.0 means double size.


@dataclass(frozen=True)
class PollOption:
    text: str  # Option text, 1-100 characters
    voter_count: int  # Number of users that voted for this option


@dataclass(frozen=True)
class ShippingAddress:
    country_code: str  # ISO 3166-1 alpha-2 country code
    state: str
    city: str
    street_line1: str
    street_line2: str
    post_code: str


@dataclass(frozen=True)
class EncryptedCredentials:
    '''
    Contains data required for decrypting and authenticating.
    See https://core.telegram.org/passport#receiving-information
    '''
    data: str  # Base64-encoded encrypted JSON-serialized data 
               # with unique user's payload, data hashes and 
               # secrets required for `EncryptedPassportElement`
               # decryption and authentication
    hash: str  # Base64-encoded data hash for data authentication
    secret: str  # Base64-encoded secret, encrypted with the bot's
                 # public RSA key, required for data decryption


@dataclass(frozen=True)
class PassportFile:
    '''
    This object represents a file uploaded to Telegram Passport.
    Currently all Telegram Passport files are in JPEG format when
    decrypted and don't exceed 10MB
    '''
    file_id: str
    file_size: int
    file_date: int  # Unix time when the file was uploaded


@dataclass(frozen=True)
class Invoice:
    title: str  # Product name
    description: str
    start_parameter: str  # Unique bot deep-linking parameter that can be
                          # used to generate this invoice
    currency: str  # Three-letter ISO 4217 currency code
    total_amount: int  # Total price in the smallest units of the currency
                       # (integer, not float/double). For example, for a
                       # price of US$ 1.45 pass amount = 145.
                       # See the exp parameter in currencies.json,
                       # https://core.telegram.org/bots/payments/currencies.json
                       # it shows the number of digits past the decimal point
                       # for each currency (2 for the majority of currencies).


@dataclass(frozen=True)
class Location:
    longitude: float
    latitude: float


@dataclass(frozen=True)
class Contact:
    phone_number: str
    first_name: str
    last_name: str = None
    user_id: int = None
    vcard: str = None  # https://en.wikipedia.org/wiki/VCard


@dataclass(frozen=True)
class PhotoSize:
    file_id: str
    width: int
    height: int
    file_unique_id: str = None
    file_size: int = None


@dataclass(frozen=True)
class Voice:
    file_id: str
    duration: int  # Duration of the audio in seconds as defined by sender
    file_unique_id: str = None
    mime_type: str = None
    file_size: int = None


@dataclass(frozen=True)
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: str = None
    username: str = None
    language_code: str = None  # IETF language tag of the user's language
                               # https://en.wikipedia.org/wiki/IETF_language_tag


@dataclass
class OrderInfo:
    name: str = None
    phone_number: str = None
    email: str = None
    shipping_address: ShippingAddress = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class EncryptedPassportElement:
    '''
    Contains information about documents or other Telegram Passport elements
    shared with the bot by the user.
    '''
    type: str  # Element type. One of “personal_details”, “passport”,
               # “driver_license”, “identity_card”, “internal_passport”,
               # “address”, “utility_bill”, “bank_statement”,
               # “rental_agreement”, “passport_registration”,
               # “temporary_registration”, “phone_number”, “email”.
    hash: str  # Base64-encoded element hash for using in `PassportElementErrorUnspecified`
    data: str = None
    phone_number: str = None
    email: str = None
    files: List[PassportFile] = None
    front_side: PassportFile = None
    reverse_side: PassportFile = None
    selfie: PassportFile = None
    translation: List[PassportFile] = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class CallbackGame:
    pass


@dataclass
class InlineKeyboardButton:
    text: str
    url: str = None
    login_url: str = None
    callback_data: str = None
    switch_inline_query: str = None
    switch_inline_query_current_chat: str = None
    callback_game: CallbackGame = None
    pay: bool = None

    def __post_init__(self):
        init_dataclass_fields(self)

@dataclass
class PassportData:
    data: List[EncryptedPassportElement]
    credentials: EncryptedCredentials

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class SuccessfulPayment:
    currency: str
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    shipping_option_id: str = None
    order_info: OrderInfo = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Poll:
    id: str
    question: str
    options: List[PollOption]
    is_closed: bool

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Venue:
    location: Location
    title: str
    address: str
    foursquare_id: str = None
    foursquare_type: str = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class VideoNote:
    file_id: str
    length: int
    duration: int
    thumb: PhotoSize = None
    file_size: int = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Video:
    file_id: str
    width: int
    height: int
    duration: int
    thumb: PhotoSize = None
    mime_type: str = None
    file_size: int = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Sticker:
    file_id: str
    width: int
    height: int
    thumb: PhotoSize = None
    emoji: str = None
    set_name: str = None
    mask_position: MaskPosition = None
    file_size: int = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Animation:
    file_id: str
    width: int
    height: int
    duration: int
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class PreCheckoutQuery:
    id: str
    from_user: User
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: str = None
    order_info: OrderInfo = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class ShippingQuery:
    '''
    This object contains information about an incoming shipping query.
    '''
    id: str
    from_user: User
    invoice_payload: str
    shipping_address: ShippingAddress

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class ChosenInlineResult:
    '''
    Represents a result of an inline query that was chosen by the user and sent to
    their chat partner.
    '''
    result_id: str
    from_user: User
    query: str
    location: Location = None
    inline_message_id: str = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class InlineQuery:
    id: str
    from_user: User
    query: str
    offset: str
    location: Location = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class MessageEntity:
    type: str
    offset: int
    length: int
    url: str = None
    user: User = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Game:
    title: str
    decription: str
    photo: List[PhotoSize]
    text: str = None
    text_entities: List[MessageEntity] = None
    animation: Animation = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Document:
    file_id: str
    file_unique_id: str = None
    thumb: PhotoSize = None
    file_name: str = None
    mime_type: str = None
    file_size: int = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Audio:
    file_id: str
    duration: int
    performer: str = None
    title: str = None
    mime_type: str = None
    file_size: int = None
    thumb: PhotoSize = None

    def __post_init__(self):
        init_dataclass_fields(self)


class Message:  # HACK. Because `Message` class has link to itself
    pass


@dataclass
class Chat:
    id: int
    type: str
    title: str = None
    username: str = None
    first_name: str = None
    last_name: str = None
    all_members_are_administrators: bool = None
    photo: ChatPhoto = None
    description: str = None
    invite_link: str = None
    pinned_message: Message = None
    sticker_set_name: str = None
    can_set_sticker_set: bool = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Message:
    message_id: int
    date: int
    from_user: User = None
    chat: Chat = None
    forward_from: User = None
    forward_from_chat: Chat = None
    forward_from_message_id: int = None
    forward_signature: str = None
    forward_sender_name: str = None
    forward_date: int = None
    reply_to_message: Message = None
    edit_date: int = None
    media_group_id: str = None
    author_signature: str = None
    text: str = None
    entities: List[MessageEntity] = None
    caption_entities: List[MessageEntity] = None
    audio: Audio = None
    document: Document = None
    animation: Animation = None
    game: Game = None
    photo: List[PhotoSize] = None
    sticker: Sticker = None
    video: Video = None
    voice: Voice = None
    video_note: VideoNote = None
    caption: str = None
    contact: Contact = None
    location: Location = None
    venue: Venue = None
    poll: Poll = None
    new_chat_members: List[User] = None
    left_chat_member: User = None
    new_chat_title: str = None
    new_chat_photo: List[PhotoSize] = None
    delete_chat_photo: bool = None
    group_chat_created: bool = None
    supergroup_chat_created: bool = None
    channel_chat_created: bool = None
    migrate_to_chat_id: int = None
    migrate_from_chat_id: int = None
    pinned_message: Message = None
    invoice: Invoice = None
    successful_payment: SuccessfulPayment = None
    connected_website: str = None
    passport_data: PassportData = None

    # Inline keyboard attached to the message. login_url buttons are represented
    # as ordinary url buttons.
    reply_markup: List[List[InlineKeyboardButton]] = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class CallbackQuery:
    id: str
    from_user: User
    chat_instance: str
    message: Message = None
    inline_message_id: str = None
    data: str = None
    game_short_name: str = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class Update:
    update_id: int
    message: Message = None
    edited_message: Message = None
    channel_post: Message = None
    edited_channel_post: Message = None
    inline_query: InlineQuery = None
    chosen_inline_result: ChosenInlineResult = None
    callback_query: CallbackQuery = None
    shipping_query: ShippingQuery = None
    pre_checkout_query: PreCheckoutQuery = None
    poll: Poll = None

    def __post_init__(self):
        fields = ('message', 'callback_query', 'inline_query',
                  'shipping_query', 'pre_checkout_query',
                  'chosen_inline_result')
        for name in fields:
            value = getattr(self, name)
            if value is not None and 'from' in value:
                value['from_user'] = value['from']
                del value['from']
            setattr(self, name, value)
        init_dataclass_fields(self)
