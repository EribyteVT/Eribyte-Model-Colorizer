from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.type import CustomRewardRedemptionStatus
from twitchAPI.type import AuthScope
import asyncio
from SECRETS import APP_ID, APP_SECRET
import pyvts
import time
from threading import *      
import re


lock = Semaphore(1)

TARGET_SCOPES = [AuthScope.MODERATOR_READ_FOLLOWERS,AuthScope.CHANNEL_MANAGE_REDEMPTIONS]

plugin_info = {
        "plugin_name": "Eri Palette Swapper",
        "developer": "Eribyte",
        "authentication_token_path": r"C:\Users\Eribyte\Desktop\custom_palette_codin\token.txt"
    }
vts = pyvts.vts(plugin_info=plugin_info)

twitch = None

async def accept(data):
    await twitch.update_redemption_status(data['subscription']['condition']['broadcaster_user_id'],data['subscription']['condition']['reward_id'], data['event']['id'],CustomRewardRedemptionStatus.FULFILLED)


async def refund(data):
     await twitch.update_redemption_status(data['subscription']['condition']['broadcaster_user_id'],data['subscription']['condition']['reward_id'], data['event']['id'],CustomRewardRedemptionStatus.CANCELED)

# listen_channel_points_custom_reward_redemption_add
async def Darkbyte(data: ChannelPointsCustomRewardRedemptionAddEvent):
    data = data.to_dict()

    print(data)

    #get lock
    if(not lock.acquire(blocking=False)):
        print("CURRENTLY LOCKED")
        await refund(data)
        return

    await vts.connect()
    await vts.request_authenticate_token()  # get token
    await vts.request_authenticate()  # use token

    #lasts 20 seconds
    # 3* 5 = 15 sleeps 20 seconds each
    total_sec = 300
    splits = 300

    time_per_split = total_sec//splits

    hair_names = ["R","ArtMesh","ArtMesh0","L","STRIP","R15","R16","R17","L15","L16","L17","IN","ArtMesh2","ArtMesh13"]

    ear_names = ["R5","R18"]

    eye_names = ["ArtMesh50","ArtMesh19"]

    #vts returns to normal if we don't do this, unknown why
    for i in range(splits):
        await vts.request(
            vts.vts_request.ColorTintRequest(red = 255,name_exact=eye_names)
        )
        await vts.request(
            vts.vts_request.ColorTintRequest(red=50,green=50,blue=50,name_exact=hair_names + ear_names)
        )

        
        time.sleep(time_per_split)
    #back to normal at the end
    await vts.request(
            vts.vts_request.ColorTintRequest(red=255,green=255,blue=255,name_exact=eye_names)
        )
    
    await vts.request(
        vts.vts_request.ColorTintRequest(red=255,green=255,blue=255,name_exact=hair_names + ear_names)
    )

    #release our locks
    await accept(data)
    lock.release() 


async def customHairColor(data: ChannelPointsCustomRewardRedemptionAddEvent):
    data = data.to_dict()
    #get lock
    if(not lock.acquire(blocking=False)):
        print("CURRENTLY LOCKED")
        await refund(data)
        return


    await vts.connect()
    await vts.request_authenticate_token()  # get token

    try:
        await vts.request_authenticate()  # use token
    except:
        pass

    x = re.search("[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}",  data['event']['user_input']) 

    try:
        rgbString = x.string
        colors = rgbString.split(',')
        red = int(colors[0])
        green = int(colors[1])
        blue = int(colors[2])
    except:
        #auto cancel code if malformed
        await refund(data)
        print("invalid code")
        lock.release()
        return

    if(red >255 or red <0 or green > 255 or green < 0 or blue >255 or blue <0):
        await refund(data)
        print("invalid code")
        lock.release()
        return


    total_sec = 300
    splits = 300

    time_per_split = total_sec//splits

    hair_names = ["R","ArtMesh","ArtMesh0","L","STRIP","R15","R16","R17","L15","L16","L17","IN","ArtMesh2","ArtMesh13"]

    ear_names = ["R5","R18"]

    #jank solution, no clue why it works
    for i in range(splits):
        await vts.request(
            vts.vts_request.ColorTintRequest(red=red,green=green,blue=blue,name_exact=hair_names + ear_names)
        )
        
        time.sleep(time_per_split)
    
    await vts.request(
        vts.vts_request.ColorTintRequest(red=255,green=255,blue=255,name_exact=hair_names + ear_names)
    )

    await accept(data)
    lock.release() 

async def customEyeColor(data: ChannelPointsCustomRewardRedemptionAddEvent):
    data = data.to_dict()

    #get lock
    if( not lock.acquire(blocking=False)):
        print("CURRENTLY LOCKED")
        await refund(data)
        return

    

    await vts.connect()
    await vts.request_authenticate_token()  # get token
    await vts.request_authenticate()  # use token

    #make sure it's 'rrr,ggg,bbb' exactly
    x = re.search("[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}",  data['event']['user_input']) 

    try:
        rgbString = x.string
        colors = rgbString.split(',')
        red = int(colors[0])
        green = int(colors[1])
        blue = int(colors[2])
    except:
        #auto cancel code if malformed
        await refund(data)
        print("invalid code")
        lock.release()
        return

    if(red >255 or red <0 or green > 255 or green < 0 or blue >255 or blue <0):
        await refund(data)
        print("invalid code")
        lock.release()
        return

    total_sec = 300
    splits = 300

    time_per_split = total_sec//splits

    eye_names = ["ArtMesh50","ArtMesh19"]

    for i in range(splits):
        await vts.request(
            vts.vts_request.ColorTintRequest(red=red,green=green,blue=blue,name_exact=eye_names)
        )
        time.sleep(time_per_split)

    await vts.request(
        vts.vts_request.ColorTintRequest(red=255,green=255,blue=255,name_exact=eye_names)
    )

    #release eye lock
    await accept(data)
    lock.release() 


async def run():
    global twitch
    # create the api instance and get user auth either from storage or website
    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    await helper.bind()

    # get the currently logged in user
    user = await first(twitch.get_users())
    print(user.id)

    # create eventsub websocket instance and start the client.
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    #listen for redeems
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=Darkbyte, reward_id='8e4cb221-ccbf-477d-a7c6-993575c21a72')
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=customHairColor, reward_id='6d07918a-1aa0-4337-947b-f2303e19af48')
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=customEyeColor, reward_id='f049cb4d-9199-4178-9165-032faf81e7c2')
    

    # eventsub will run in its own process
    # so lets just wait for user input before shutting it all down again
    try:
        input('press Enter to shut down...')
    except KeyboardInterrupt:
        pass
    finally:
        # stopping both eventsub as well as gracefully closing the connection to the API
        await eventsub.stop()
        await twitch.close()


asyncio.run(run())