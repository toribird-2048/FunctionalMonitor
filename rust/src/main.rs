use macroquad::prelude::*;
use chrono::{Local, };

fn render_text(text: &str,x:f32, y:f32, font: Option<&Font>, font_size: u16) {
    let size = measure_text(text, font, font_size, 1.0);
    draw_text_ex(
        text,
        x - size.width / 2.0,
        y + size.offset_y / 2.0,
        TextParams {
            font: font,
            font_size: font_size,
            color: WHITE,
            ..Default::default()
        }
    );
}

trait Ui {
    fn draw(&self);
}

struct ClockUi;

impl Ui for ClockUi {
    fn draw(&self) {
        let now_local = Local::now();
        render_text(
            &now_local.format("%H:%M:%S %m/%d %a").to_string(),
            screen_width() / 2.0,
            screen_height() / 2.0, 
            None, 200
        );
    }
}

#[macroquad::main("Functional Monitor")]
async fn main() {
    let clock_ui = ClockUi;
    loop {
        clear_background(BLACK);
        clock_ui.draw();
        next_frame().await
    }
}
