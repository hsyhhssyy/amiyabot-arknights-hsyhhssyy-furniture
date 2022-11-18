import os
import asyncio
import re

from amiyabot import PluginInstance
from amiyabot.network.download import download_async

from core import log, Message, Chain
from core.util import get_index_from_text,create_dir
from core.resource.arknightsGameData.common import JsonData

curr_dir = os.path.dirname(__file__)

class FurniturePluginInstance(PluginInstance):
    def install(self):
        asyncio.create_task(init_furnitures())
        pass

bot = FurniturePluginInstance(
    name='兔兔查询家具',
    version='1.0',
    plugin_id='amiyabot-arknights-hsyhhssyy-furniture',
    plugin_type='',
    description='查询家具相关信息',
    document=f'{curr_dir}/README.md'
)

class FurnitureData:
    def initialize(cls):
        cls.furniture_sets = {}

class Furniture:
    def __init__(self, code: str, data: dict):
        self.id = code
        self.name = data['name']
        self.description = data['description']
        self.usage = data['usage']
        self.comfort = data['comfort']

class FurnitureSet:
    def __init__(self, code: str, data: dict, furnitures : list ):
        self.id = code
        self.furnitures = []
        self.name = data['name']
        self.description = data['desc']
        self.furnitures = furnitures

async def download_wiki_image(file_name, html_key, local_dir, local_file):
    async with log.catch('wiki download error:'):            
        front_page_address = f'https://prts.wiki/w/文件:{file_name}'
        res = str(await download_async(front_page_address) , encoding='utf-8') 
        if res:
            # 正则解析 
            match_result = re.search(f'<div class="fullMedia"><p><a href="([\s\S]*?)" class="internal" title="([\s\S]*?)">{html_key}</a>', res)
            
            original_url = f'https://prts.wiki/{match_result.group(1)}'
            image_res = await download_async(original_url)
            if image_res:
                create_dir(f'{local_dir}')
                with open(f'{local_dir}/{local_file}', mode='wb+') as src:
                    src.write(image_res)
                log.info(f'wiki image downloaded:{local_dir}/{local_file}')
                return f'{local_dir}/{local_file}'

async def init_furnitures():

    try:

        building_data = JsonData.get_json_data('building_data')
        furniset_data = building_data['customData']['themes']

        furni_data = building_data['customData']['furnitures']

        furniture_sets = {}

        for funiset_id in furniset_data.keys():
            furniset = furniset_data[funiset_id]

            furni_keys = furniset['furnitures']
            furni_list = []
            for furni_id in furni_keys:
                furni = furni_data[furni_id]
                furni_list.append(
                    Furniture(furni_id,furni)
                )

            furniture_sets[funiset_id] = FurnitureSet(code=funiset_id,data=furniset,furnitures = furni_list)
        
        FurnitureData.furniture_sets = furniture_sets

        if not os.path.exists('resource/hsyhhssyy/furniture'):
            create_dir('resource/hsyhhssyy/furniture')

        log.info('init furniture data...')
    
    except Exception as e :
        log.info(f'except:{e}')

@bot.on_message(keywords=['家具'],level=5)
async def _(data: Message):

    # 判断是否拥有家具名字和家具列表
    # 直接列出家具列表

    furniset_list = []

    for furniset_id in FurnitureData.furniture_sets.keys():
        furniset_list.append(FurnitureData.furniture_sets[furniset_id])

    text = f'博士，这是目前可以获得的所有家具套装的列表\n\n'
    for i, furniset in enumerate(furniset_list):
        text += f'[{i + 1}] %s\n' % furniset.name

    text += '\n回复【序号】查询对应的家具套装资料'

    wait = await data.wait(Chain(data).text(text))
    if wait:
        index = get_index_from_text(wait.text_digits, furniset_list)

    furniset_item = {}

    if index is not None:
        furniset = furniset_list[index]
        furniset_item['id'] = furniset.id
        furniset_item['name'] = furniset.name
        furniset_item['description'] = furniset.description
        furniset_item['funitures'] = []

        #确认图片
        furniset_image_path = f'resource/hsyhhssyy/furniture/furset_{furniset.id}.png'
        if not os.path.exists(furniset_image_path):
            # 改为从Wiki获取该文件
            furniset_image_path = await download_wiki_image(f'主题_{furniset.name}.png',f'主题_{furniset.name}.png','resource/hsyhhssyy/furniture',f'furset_{furniset.id}.png')
        furniset_item['image'] = furniset_image_path

        for furni in furniset.furnitures:
            furni_i = {}
            furni_i['id'] = furni.id
            furni_i['name'] = furni.name
            furni_i['comfort'] = furni.comfort
            furni_i['description'] = furni.description
            furni_image_path = f'resource/hsyhhssyy/furniture/fur_{furni.id}.png'
            if not os.path.exists(furni_image_path):
                # 改为从Wiki获取该文件
                furni_image_path = await download_wiki_image(f'家具_{furni.name}.png',f'家具_{furni.name}.png','resource/hsyhhssyy/furniture',f'fur_{furni.id}.png')
            furni_i['image'] = furni_image_path

            furniset_item['funitures'].append(furni_i)
    

    return Chain(data).html(f'{curr_dir}/template/furniture_set.html', furniset_item) 