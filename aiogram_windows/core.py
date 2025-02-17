from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from typing import Union, Optional, Callable
from inspect import iscoroutine

INLINE_BUTTON_KEYS = (
    "url", "login_url", "callback_data", "switch_inline_query", "switch_inline_query_current_chat", "callback_game",
    "pay")
REPLY_BUTTON_KEYS = ("request_contact", "request_location", "request_poll")
BUTTONS_ARGS = INLINE_BUTTON_KEYS + REPLY_BUTTON_KEYS


class ProgressBar:
    def __init__(self,
                 text: str,
                 minimum: int = 0,
                 maximum: int = 100,
                 position: int = 0,
                 background: str = "░",
                 progress: str = "█",
                 wight: int = 10,
                 decimals: int = 1,
                 imposition: bool = False,
                 revers: bool = False,
                 vertical: bool = False
                 ):
        self._text = text
        self.minimum = minimum
        self.maximum = maximum
        self.position = position
        self.background = background
        self.progress = progress
        self.wight = wight
        self.decimals = decimals
        self.imposition = imposition
        self.revers = revers
        self.vertical = vertical
        if self.imposition:
            if len(self.progress) != len(self.background):
                raise Exception("")  # todo
            self.wight = len(self.progress)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos: int):
        if pos > self.maximum:
            pos = self.maximum
        elif pos < self.minimum:
            pos = self.minimum
        self._position = pos

    @property
    def text(self) -> str:
        text = self._text
        if "{progress}" in text:
            fill = int(self.wight * self.position // self.maximum)
            if self.imposition:
                if self.position == 0:
                    bar = self.background
                else:
                    bar = self.progress[:fill] + self.background[fill:]
            else:
                bar = self.progress * fill + self.background * (self.wight - fill)
            if self.revers:
                bar = bar[::-1]
            if self.vertical:
                bar = "\n".join(list(bar))
            text = text.replace("{progress}", bar)
        if "{%}" in text:
            percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.position / float(self.maximum)))
            text = text.replace("{%}", percent)
        return text

    def __str__(self):
        return self.text

    def __call__(self, *args, **kwargs):
        return self.text

    @text.setter
    def text(self, text: str):
        self._text = text


class Button:
    def __init__(self,
                 text: str, callback_data: types.base.String = None,
                 on_click: Optional[Callable] = None,
                 visible: Optional[Union[bool, Callable]] = True,
                 url: types.base.String = None,
                 login_url: types.login_url.LoginUrl = None,
                 switch_inline_query: types.base.String = None,
                 switch_inline_query_current_chat: types.base.String = None,
                 callback_game: types.callback_game.CallbackGame = None,
                 pay: types.base.Boolean = None,
                 request_contact: types.base.Boolean = None,
                 request_location: types.base.Boolean = None,
                 request_poll: types.reply_keyboard.KeyboardButtonPollType = None,
                 # **kwargs  # todo delete
                 ):
        self.text = text
        #  self.kwargs = kwargs  # todo delete
        self.kwargs = {key: value for key, value in locals().items() if value is not None and key in BUTTONS_ARGS}
        self.on_click = on_click
        self.visible = visible
        self.registered = False  # todo delete
        self.is_inline()
        # if "callback_data" not in self.kwargs:
        #    self.kwargs["callback_data"] = self.text.__str__()   # todo Deprecated

    @property
    def button(self):
        if self.is_inline():
            return types.InlineKeyboardButton(text=self.text.__str__(), **self.kwargs)
        else:
            return types.KeyboardButton(text=self.text.__str__(), **self.kwargs)

    @property
    def row(self):
        setattr(self, "__new_line", None)
        return self

    def is_inline(self):
        if len(self.kwargs) > 1:
            raise Exception("")  # todo
        return any(key in INLINE_BUTTON_KEYS for key, val in self.kwargs.items())

    def __call__(self, update: Union[types.CallbackQuery, types.Message]):
        if self.is_inline():
            return update.data == self.kwargs.get("callback_data")
        else:
            return update.text == self.text

    def __eq__(self, other: Union[types.CallbackQuery, types.Message]):
        if self.is_inline():
            return other == self.kwargs.get("callback_data")
        else:
            return other == self.text


class Input:
    def __init__(self, *filters, on_enter: callable = None, on_wrong: callable = None, **kwargs):
        self.args = filters
        self.kwargs = kwargs
        self.on_enter = on_enter
        self.on_wrong = on_wrong
        self.registered = False


class Window:
    text: str = "text"
    state: str = None
    save_data: bool = True
    data_name: str = None
    window_name: str = "Window"
    dispatcher: Dispatcher = None
    row_width: int = 3
    schema: list = None
    default_save: bool = True
    multiselect: bool = False
    auto_handlers: bool = False

    @classmethod
    async def register_child_callbacks(cls, dispatcher: Dispatcher = None):
        dispatcher = dispatcher or cls.dispatcher
        if dispatcher is None:
            raise Exception("dispatcher not set")
        for child in Window.__subclasses__():
            child.register_callbacks(dispatcher=dispatcher)

    @classmethod
    async def next(cls, data: Union[types.CallbackQuery, types.Message] = None):
        state = Dispatcher.get_current().current_state()
        state_name = await state.get_state()
        cur_state = cls.get_window(state_name)

        try:
            next_step = cls.__subclasses__().index(cur_state) + 1
        except ValueError:
            next_step = 0

        try:
            next_state = cls.__subclasses__()[next_step]
        except IndexError:
            return
        await next_state.show(chat=state.chat, user=state.user)

    @classmethod
    async def previous(cls, data: Union[types.CallbackQuery, types.Message] = None):
        state = Dispatcher.get_current().current_state()
        state_name = await state.get_state()
        cur_state = cls.get_window(state_name)

        try:
            previous_step = cls.__subclasses__().index(cur_state) - 1
        except ValueError:
            previous_step = 0

        if previous_step < 0:
            previous_step = 0
        try:
            next_state = cls.__subclasses__()[previous_step]
        except IndexError:
            return
        await next_state.show(chat=state.chat, user=state.user)

    @classmethod
    async def first(cls, data: Union[types.CallbackQuery, types.Message] = None):
        state = Dispatcher.get_current().current_state()
        first_step_name = cls.__subclasses__()[0]
        await first_step_name.show(chat=state.chat, user=state.user)

    @classmethod
    async def last(cls, data: Union[types.CallbackQuery, types.Message] = None):
        state = Dispatcher.get_current().current_state()
        first_step_name = cls.__subclasses__()[-1]
        await first_step_name.show(chat=state.chat, user=state.user)

    @classmethod
    def set_dispatcher(cls, dispatcher: Dispatcher):
        cls.dispatcher = dispatcher

    @classmethod
    def get_window(cls, name: str):
        for sub_cls in Window.__subclasses__():
            if sub_cls.state == name:
                return sub_cls
        return None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.state = f"{cls.window_name}:{cls.__name__}"
        if cls.data_name is None:
            cls.data_name = cls.state
        if cls.auto_handlers:
            cls.register_callbacks()

    @classmethod
    def add(cls, other):
        if isinstance(other, list):
            i = 0
            for but in other:
                name = f"{cls.window_name}{i}"
                while hasattr(cls, name):
                    i += 1
                    name = f"{cls.window_name}_{i}"
                else:
                    setattr(cls, name, but)
        elif isinstance(other, dict):
            i = 0
            for n, but in other.items():
                name = n
                while hasattr(cls, name):
                    i += 1
                    name = f"{n}{i}"
                else:
                    setattr(cls, name, but)
        elif isinstance(other, (Button, Input)):
            i = 0
            name = f"{cls.window_name}{i}"
            while hasattr(cls, name):
                i += 1
                name = f"{cls.window_name}_{i}"
            else:
                setattr(cls, name, other)

    @classmethod
    async def build_buttons(cls):
        buttons = []
        rows = []
        n = 0
        for j in vars(cls):
            data: Button = getattr(cls, j)
            if isinstance(data, Button):
                if callable(data.visible):
                    visible = data.visible()
                elif iscoroutine(data.visible):
                    visible = await data.visible()
                else:
                    visible = data.visible
                if not visible:
                    continue
                n += 1
                buttons.append(data)
                if hasattr(data, "__new_line"):
                    rows.append(n)
                    n = 0
        if cls.schema:
            schema = cls.schema
        elif rows:
            schema = rows
        else:
            schema = (cls.row_width,)
        if not buttons:
            return None
        if buttons[0].is_inline():
            keyboard = types.InlineKeyboardMarkup()
        else:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        schema_line = 0
        row = []
        for i in buttons:
            row.append(i.button)
            if len(row) == schema[schema_line]:
                keyboard.row(*row)
                row = []
                schema_line += 1
                if schema_line >= len(schema):
                    schema_line -= 1
        else:
            if row:
                keyboard.row(*row)
        return keyboard

    @classmethod
    async def default_callback_save(cls, call: types.CallbackQuery, state: FSMContext):
        await call.answer(cache_time=0)
        state_name = await state.get_state()
        name = cls.get_window(state_name)
        async with state.proxy() as proxy:
            if cls.multiselect:
                proxy.setdefault(name.data_name, set()).add(call.data)
            else:
                proxy.setdefault(name.data_name, call.data)

    @classmethod
    async def save_callback_data(cls, call: types.CallbackQuery, name: str = None, dispatcher: Dispatcher = None):
        dispatcher = dispatcher or cls.dispatcher
        if dispatcher is None:
            raise Exception("dispatcher not set")
        name = cls if name is None else cls.get_window(name=name)
        if name is None:
            return
        async with FSMContext(
                storage=dispatcher.storage,
                chat=call.message.chat.id,
                user=call.from_user.id).proxy() as proxy:
            if cls.multiselect:
                proxy.setdefault(name.data_name, set()).add(call.data)
            else:
                proxy[name.data_name] = call.data

    @classmethod
    async def default_text_save(cls, message: types.Message, state: FSMContext):
        state_name = await state.get_state()
        name = cls.get_window(state_name)
        async with state.proxy() as proxy:
            proxy[name.data_name] = message.text

    @classmethod
    def register_callbacks(cls, dispatcher: Dispatcher = None):
        dispatcher = dispatcher or cls.dispatcher
        if dispatcher is None:
            raise Exception("dispatcher not set")
        for i in vars(cls):
            data: Union[Button, Input] = getattr(cls, i)
            if isinstance(data, Button) and not data.registered:
                if cls.default_save:
                    if data.is_inline():
                        dispatcher.register_callback_query_handler(
                            callback=(cls.default_callback_save if data.on_click is None else data.on_click),
                            text=data.kwargs.get("callback_data"),
                            state=cls.state
                        )
                    else:
                        dispatcher.register_message_handler(
                            callback=(cls.default_text_save if data.on_click is None else data.on_click),
                            text=data.text,
                            state=cls.state
                        )
            elif isinstance(data, Input) and not data.registered:
                dispatcher.register_message_handler(
                    (cls.default_text_save if data.on_enter is None else data.on_enter),
                    *data.args,
                    state=cls.state,
                    **data.kwargs
                )
                if data.on_wrong is not None:
                    dispatcher.register_message_handler(
                        callback=data.on_wrong,
                        state=cls.state
                    )

    @classmethod
    async def show(cls,
                   data: Union[types.CallbackQuery, types.Message] = None,
                   chat: str = None,
                   user: str = None,
                   dispatcher: Dispatcher = None):
        dispatcher = dispatcher or cls.dispatcher
        if dispatcher is None:
            raise Exception("dispatcher not set")
        if data is not None:
            if isinstance(data, types.CallbackQuery):
                await data.answer(cache_time=0)
                chat, user = data.message.chat.id, data.from_user.id
                if cls.save_data:
                    name = await dispatcher.storage.get_state(chat=chat, user=user)
                    await cls.save_callback_data(call=data, name=name)
            elif isinstance(data, types.Message):
                chat, user = data.chat.id, data.from_user.id
                await cls.default_text_save(message=data, state=Dispatcher.get_current().current_state())
            else:
                raise Exception("UNKNOWN")
        elif chat is None or user is None:
            raise Exception("need chat and/or user")
        await dispatcher.storage.set_state(chat=chat, user=user, state=cls.state)
        keyboard = await cls.build_buttons()
        await dispatcher.bot.send_message(
            chat_id=chat,
            text=cls.text(chat=chat, user=user, dispatcher=dispatcher) if callable(cls.text) else cls.text,
            reply_markup=keyboard
        )
