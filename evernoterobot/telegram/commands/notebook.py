
async def notebook(robot, chat_id, telegram):
    user_id = robot.user.id
    access_token = await robot.get_evernote_access_token(user_id)
    notebooks = robot.evernote.list_notebooks(access_token)
    text = "\n".join([n.name for n in notebooks])
    await telegram.sendMessage(chat_id, text)
