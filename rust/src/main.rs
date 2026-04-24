use macroquad::prelude::*;
use chrono::{Local, };

fn render_text(text:&str,x:f32, y:f32, font: Option<&Font>, font_size: u16, line_space: f32) {
    let texts: Vec<&str> = text.split("\n").collect();
    let dims: Vec<TextDimensions> = texts.iter().map(|x| measure_text(x, font, font_size, 1.0)).collect();
    let total_height = dims.iter().map(|d| d.height).sum::<f32>() + line_space * (texts.len() as f32 - 1.0);
    let mut current_y_top = y - total_height / 2.0;
    for (i, line) in texts.iter().enumerate() {
        let size = dims[i];
        draw_text_ex(
            line,
            x - size.width / 2.0,
            current_y_top + size.offset_y,
            TextParams {
                font: font,
                font_size: font_size,
                color: WHITE,
                ..Default::default()
            }
        );
        current_y_top += size.height + line_space;
    }
}

trait Ui {
    fn draw(&self);
}

struct ClockUi;

impl Ui for ClockUi {
    fn draw(&self) {
        let now_local = Local::now();
        render_text(
            &now_local.format("%H:%M:%S\n%m/%d %a").to_string(),
            screen_width() / 2.0,
            screen_height() / 2.0,
            None, 200,
            30.0
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
