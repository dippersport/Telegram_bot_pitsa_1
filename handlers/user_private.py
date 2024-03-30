# from aiogram import F, types, Router
# from aiogram.enums import ParseMode
# from aiogram.filters import CommandStart, Command, or_f
# from aiogram.utils.formatting import as_list, as_marked_section, Bold #Italic, as_numbered_list и тд 

# from filters.chat_types import ChatTypeFilter

# from kbds.reply import get_keyboard
# from kbds import reply

# user_private_router = Router()
# user_private_router.message.filter(ChatTypeFilter(["private"]))


# @user_private_router.message(CommandStart())
# async def start_cmd(message: types.Message):
#     await message.answer(
#         "Привет, я виртуальный помощник",
#         reply_markup=get_keyboard(
#             "Меню",
#             "О магазине",
#             "Варианты оплаты",
#             "Варианты доставки",
#             placeholder="Что вас интересует?",
#             sizes=(2, 2)
#         ),
#     )


# # @user_private_router.message(F.text.lower() == "меню")
# @user_private_router.message(or_f(Command("menu"), (F.text.lower() == "меню")))
# async def menu_cmd(message: types.Message):

#     text = as_marked_section(
#             Bold("Меню пиццерии: "),
#             "Маргарита: Соус томатный, моцарелла, помидоры, базилик.",
#             "Пепперони: Соус томатный, моцарелла, пепперони.",
#             "Гавайская: Соус томатный, моцарелла, ветчина, ананасы.",
#             "Четыре сыра: Соус сливочный, моцарелла, пармезан, горгонзола, дор-блю.",
#             "Вегетарианская: Соус томатный, моцарелла, шампиньоны, перец, лук, оливки.",
#             "Мексиканская: Соус томатный, моцарелла, фарш говяжий, острый перец, лук, перец чили.",
#             "Кальцоне: Соус томатный, моцарелла, ветчина, грибы, помидоры, лук, перец.",
#             marker='✅, 🤗 '
#         )

#     await message.answer(text.as_html())


# @user_private_router.message(F.text.lower() == "о магазине")
# @user_private_router.message(Command("about"))
# async def about_cmd(message: types.Message):

#     text = as_marked_section(
#             Bold("Магазин в центре:"),
#             "Мы работаем для вас",
#             "Ждем вас",
#             "В заведении чисто и аккуратно",
#             marker='✅, 🙂 '
#         )

#     await message.answer(text.as_html())


# @user_private_router.message(F.text.lower() == "варианты оплаты")
# @user_private_router.message(Command("payment"))
# async def payment_cmd(message: types.Message):

#     text = as_marked_section(
#             Bold("Варианты оплаты:"),
#             "Картой в боте",
#             "При получении карта/кеш",
#             "В заведении",
#             marker='✅ '
#         )
#     await message.answer(text.as_html())


# @user_private_router.message(
#     (F.text.lower().contains("доставк")) | (F.text.lower() == "варианты доставки")
# )
# @user_private_router.message(Command("shipping"))
# async def menu_cmd(message: types.Message):
#     text = as_list(
#         as_marked_section(
#             Bold("Варианты доставки/заказа:"),
#             "Курьер",
#             "Самовынос (сейчас прибегу заберу)",
#             "Покушаю у Вас (сейчас прибегу)",
#             marker='✅ '
#         ),
#         as_marked_section(
#             Bold("Нельзя:"),
#             "Почта",
#             "Голуби",
#             marker='❌ '
#         ),
#         sep='\n----------------------\n'
#     )
#     await message.answer(text.as_html())


# @user_private_router.message(F.contact)
# async def get_contact(message: types.Message):
#     await message.answer(f"номер получен")
#     await message.answer(str(message.contact))


# @user_private_router.message(F.location)
# async def get_location(message: types.Message):
#     await message.answer(f"локация получена")
#     await message.answer(str(message.location))
from aiogram import F, types, Router
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import (
    orm_add_to_cart,
    orm_add_user,
)

from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import MenuCallBack, get_callback_btns



user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    user = callback.from_user
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None,
    )
    await orm_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer("Товар добавлен в корзину.")


@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):

    if callback_data.menu_name == "add_to_cart":
        await add_to_cart(callback, callback_data, session)
        return

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()

