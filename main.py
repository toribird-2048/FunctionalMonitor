import pygame
import sys
from notion_client import Client
import os
from typing import Dict, List
from datetime import timezone, timedelta, datetime
from dotenv import load_dotenv
from enum import Enum, auto
from get_items_data import fetch_needed_items, fetch_homework

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATA_SOURCE_ID = os.environ["NOTION_DATA_SOURCE_ID"]

SCREEN_SIZE = (1920, 1280)
JST = timezone(timedelta(hours=9))
NOTO_SANS_JP = "./fonts/NotoSansJP-VariableFont_wght.ttf"

client = Client(auth=NOTION_API_KEY)

class Positions(Enum):
    topleft = auto()
    topright = auto()
    bottomleft = auto()
    bottomright = auto()

class BaseUi:
    def __init__(self, screen:pygame.Surface):
        self.screen: pygame.Surface = screen
        self.fonts: Dict[tuple[str | None, int], pygame.Font] = {}
        
    def get_font(self, font_size:int, font_path:str|None=None) -> pygame.Font:
        font_key = (font_path, font_size)
        if font_key not in self.fonts:
            self.fonts[font_key] = pygame.Font(font_path, font_size)
        return self.fonts[font_key]
    
    def draw_center(self, text:str, font_size:int = 250, color:tuple[int, int, int]=(255,255,255)) -> None:
        font = self.get_font(font_size, None)
        text_surface: pygame.Surface = font.render(text, True, color)
        text_rect: pygame.Rect = text_surface.get_rect()
        text_rect.center = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
        self.screen.blit(text_surface, text_rect)
        
    def draw_hud(self, text:str, position:Positions, font_size:int=50, color:tuple[int, int, int]=(255,255,255)) -> None:
        font = self.get_font(font_size, NOTO_SANS_JP)
        lines = text.split("\n")
        line_height = font_size
        
        for k, line in enumerate(lines):
            text_surface: pygame.Surface = font.render(text, True, color)
            text_rect: pygame.Rect = text_surface.get_rect()
            
            if position == Positions.topleft:
                text_rect.topleft = (20, 20 + k * line_height)
            elif position == Positions.topright:
                text_rect.topright = (SCREEN_SIZE[0] - 20, 20 + k * line_height)
            elif position == Positions.bottomleft:
                text_rect.bottomleft = (20, SCREEN_SIZE[1] - 20 - (len(lines)-1-k) * line_height)
            elif position == Positions.bottomright:
                text_rect.bottomright = (SCREEN_SIZE[0] - 20, SCREEN_SIZE[1] - 20 - (len(lines)-1-k) * line_height)
            self.screen.blit(text_surface, text_rect)
        
    def draw_document(self, texts:List[str], font_size:int=50, color:tuple[int, int, int]=(255,255,255), cursor:list[int]|None=None, y_offset:int=20) -> None:
        font = self.get_font(font_size, NOTO_SANS_JP)
        line_spacing = font_size
        display_texts = [line for line in texts]
        if cursor is not None and 0 <= cursor[0] < len(texts)  and 0 <= cursor[1] <= len(texts[cursor[0]]):
            display_texts[cursor[0]] = display_texts[cursor[0]][:cursor[1]] + "|" + display_texts[cursor[0]][cursor[1]:]
        for k, line in enumerate(display_texts):
            text_surface: pygame.Surface = font.render(line, True, color)
            text_rect: pygame.Rect = text_surface.get_rect()
            text_rect.topleft = (20, y_offset + line_spacing * k)
            self.screen.blit(text_surface, text_rect)        
    
    def update(self):
        ...
    
    def draw(self):
        ...
        
    def process_event(self, event:pygame.Event):
        ...


class ClockUi(BaseUi):
    def __init__(self, screen:pygame.Surface):
        super().__init__(screen)
        self.homework_list:List[str] = fetch_homework(client)
        self.needed_items_list = fetch_needed_items(client=client)
        self.last_updated_minute_items = datetime.now(JST)
        
    def update_item_list(self):
        now_jst = datetime.now(JST)
        elapsed_time = now_jst - self.last_updated_minute_items
        
        if elapsed_time >= timedelta(minutes=1):
            self.homework_list = fetch_homework(client=client)
            self.needed_items_list = fetch_needed_items(client=client)
            self.last_updated_minute_items = now_jst
        
    def update(self):
        self.update_item_list()
    
    def draw(self):
        now_jst = datetime.now(JST)
        self.draw_center(now_jst.strftime("%m/%d(%a) %H:%M:%S"))
        self.draw_hud("\n".join(self.homework_list), Positions.topleft, font_size=75)
        self.draw_hud("\n".join(self.needed_items_list), Positions.topright, font_size=75)
        

class ItemListUi(BaseUi):
    def __init__(self, screen:pygame.Surface):
        super().__init__(screen)
        self.items_list = fetch_needed_items(client=client)
        self.last_updated_minute_items = datetime.now(JST)
        self.diary_needed_items: Dict[str, List[str]] = {
            "Sun": [],
            "Mon": ["体操服", "入試必携英作文"],
            "Tue": ["サクシード数Ⅲ", "オリジスタン数Ⅲ", "数学Ⅱ授業用ノート", "数学Ⅱ宿題用ノート"],
            "Wed": ["サクシード数Ⅲ", "オリジスタン数Ⅲ", "数学Ⅱ授業用ノート", "数学Ⅱ宿題用ノート"],
            "Thu": ["サクシード数Ⅲ", "オリジスタン数Ⅲ", "数学Ⅱ授業用ノート", "数学Ⅱ宿題用ノート", "体操服", "入試必携英作文"],
            "Fri": ["サクシード数Ⅲ", "オリジスタン数Ⅲ", "数学Ⅱ授業用ノート", "数学Ⅱ宿題用ノート"],
            "Sat": []
        }
        
    def update_item_list(self):
        now_jst = datetime.now(JST)
        elapsed_time = now_jst - self.last_updated_minute_items
        
        if elapsed_time >= timedelta(minutes=1):
            self.items_list = fetch_needed_items(client=client)
            self.last_updated_minute_items = now_jst
        
    def update(self):
        self.update_item_list()
            
    def draw(self):
        current_day = datetime.now(JST)
        next_day = current_day + timedelta(days=1)
        self.draw_document(self.diary_needed_items[next_day.strftime("%a")] + self.items_list)


class UiController:
    def __init__(self):
        self.num_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]
        self.current_ui_index = 0
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
        pygame.display.set_caption("Functional_Monitor")
        pygame.mouse.set_visible(False)
        self.uis:List[BaseUi] = [ClockUi(self.screen), ItemListUi(self.screen)]
        
    def key_event(self) -> None:
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    pygame.quit()
                    sys.exit()
                
                case pygame.Event(type=pygame.KEYDOWN):
                    if event.key == pygame.K_e:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL:
                            pygame.quit()
                            sys.exit()
                    elif event.key in self.num_keys:
                        target_idx = self.num_keys.index(event.key)
                        if target_idx < len(self.uis):
                            self.current_ui_index = target_idx
                            
                case _:
                    pass
            self.uis[self.current_ui_index].process_event(event)
            
    def update_and_draw(self):
        self.screen.fill((0,0,0))
        self.uis[self.current_ui_index].update()
        self.uis[self.current_ui_index].draw()
        pygame.display.flip()
        pygame.time.Clock().tick(60)
        
if __name__ == "__main__":
    controller = UiController()
    while True:
        controller.key_event()
        controller.update_and_draw()