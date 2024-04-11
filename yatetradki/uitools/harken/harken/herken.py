from nicegui import ui

ui.add_css('''
:root {
    --nicegui-default-padding: 1.0rem;
    --nicegui-default-gap: 0.1rem;
}
''')

def on_click():
    ui.notify('Button clicked!')

def main():
    with ui.row().classes('w-full'):
        ui.input(label='Search by word', placeholder='Type something to search').classes('w-2/12')
        a = ui.audio('https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3').classes('w-9/12')
    with ui.splitter().classes('w-full h-full') as splitter:
        with splitter.before:
            with ui.scroll_area().classes('h-dvh'):
                for i in range(30):
                    ui.label(f'file{i}.ogg')
        with splitter.after:
            with ui.scroll_area():
                for i in range(100):
                    with ui.row().classes('pl-4 hover:ring-1'):
                        ui.label('>')
                        ui.label(f'text line {i}')
    # ui.button('Click me', on_click=on_click)
    ui.run(title='herken', show=False)
    

if __name__ in {'__main__', '__mp_main__'}:
    main()