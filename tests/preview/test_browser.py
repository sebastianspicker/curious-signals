"""Rendered static-preview checks; run with make test-browser."""

from __future__ import annotations

import functools
import http.server
import os
import struct
import threading
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def preview_url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO_ROOT / "demo")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture()
def browser():
    # Deliberately fail this explicit verification lane if its dependencies are absent.
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


GUARD_APIS = """() => {
  window.forbiddenCalls = [];
  const block = name => (...args) => {
    window.forbiddenCalls.push(name);
    throw new Error('Forbidden preview API: ' + name);
  };
  for (const name of ['fetch', 'WebSocket', 'EventSource', 'XMLHttpRequest',
      'Worker', 'SharedWorker', 'Accelerometer', 'Gyroscope', 'Magnetometer',
      'AmbientLightSensor', 'AbsoluteOrientationSensor', 'RelativeOrientationSensor']) {
    Object.defineProperty(window, name, {configurable: true, value: block(name)});
  }
  for (const name of ['localStorage', 'sessionStorage', 'indexedDB', 'caches']) {
    Object.defineProperty(window, name, {configurable: true, get: block(name)});
  }
  for (const name of ['bluetooth', 'geolocation', 'mediaDevices', 'serial', 'usb', 'hid']) {
    Object.defineProperty(navigator, name, {configurable: true, get: block(name)});
  }
  Object.defineProperty(document, 'cookie', {configurable: true,
    get: block('cookie read'), set: block('cookie write')});
  navigator.sendBeacon = block('sendBeacon');
}"""


def contrast(page, selector):
    return page.locator(selector).evaluate("""element => {
      const style = getComputedStyle(element);
      const luminance = color => {
        const rgb = color.match(/[\\d.]+/g).slice(0, 3).map(Number).map(v => {
          v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        });
        return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
      };
      const a = luminance(style.color), b = luminance(style.backgroundColor);
      return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
    }""")


@pytest.mark.parametrize(
    "viewport", [{"width": 1440, "height": 1100}, {"width": 390, "height": 844}]
)
def test_preview_modes_keyboard_playback_and_runtime_boundaries(browser, preview_url, viewport):
    from playwright.sync_api import expect

    context = browser.new_context(viewport=viewport)
    context.add_init_script(f"({GUARD_APIS})();")
    page = context.new_page()
    errors, requests = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda message: (
            errors.append(message.text) if message.type in ("error", "warning") else None
        ),
    )
    page.on("request", lambda request: requests.append(request.url))
    page.clock.install()
    page.goto(preview_url)
    assert page.url == preview_url
    expect(page).to_have_title("Curious Signals · Static classroom preview")
    expect(page.get_by_role("heading", name="Temperature & humidity", exact=True)).to_be_visible()
    assert page.locator("#chart-lines polyline").count() == 2
    assert page.locator("#chart-labels text").count() == 17  # Two vertical axes.
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.evaluate("() => { fixtureValue = () => { throw new Error('Fixture recomputed'); }; }")
    for mode_id in [1, 2, 3, 4, 5, 6, 9]:
        button = page.locator(f'[data-mode="{mode_id}"]')
        button.focus()
        page.keyboard.press("Enter")
        expect(button).to_be_focused()
        expect(button).to_have_attribute("aria-pressed", "true")
        expected = page.evaluate("""() => {
          const mode = modes.find(m => m.id === state.modeId);
          return mode.series.map((_, i) =>
            fixtures.get(mode.id).series[i][120].toFixed(precisionFor(mode))
            + " " + modeUnit(mode, i));
        }""")
        assert page.locator("#readouts output").all_text_contents() == expected
        assert page.locator("#chart-lines polyline").count() == len(expected)
        assert page.locator('#readouts [aria-live="off"][aria-labelledby]').count() == len(expected)
        assert contrast(page, f'[data-mode="{mode_id}"]') >= 4.5
    start = page.locator("#toggle-stream")
    start.focus()
    assert contrast(page, "#toggle-stream") >= 4.5
    page.keyboard.press("Space")
    expect(start).to_have_text("Pause simulated stream")
    expect(page.locator("#stream-status")).to_have_text("Simulated stream started.")
    page.clock.run_for(450)
    assert page.locator("#chart-progress").inner_text() == "1.0 s fixture"
    expect(page.locator("#stream-status")).to_have_text("Simulated stream started.")
    page.keyboard.press("Space")
    expect(page.locator("#stream-status")).to_have_text("Simulated stream paused.")
    page.clock.run_for(900)
    assert page.locator("#chart-progress").inner_text() == "1.0 s fixture"
    page.keyboard.press("Tab")
    expect(page.locator("#reset-fixture")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("#stream-status")).to_have_text(
        "Simulated fixture reset. Full fixture shown."
    )
    expect(page.locator("#chart-progress")).to_have_text("24.0 s fixture")
    start.click()
    page.clock.run_for(10800)
    expect(page.locator("#stream-status")).to_have_text(
        "Simulated stream complete. Full fixture shown."
    )
    expect(start).to_have_text("Start simulated stream")
    assert page.evaluate("state.timer === null && !state.running")
    start.hover()
    assert contrast(page, "#toggle-stream") >= 4.5
    page.locator(".wordmark").focus()
    assert contrast(page, "#toggle-stream") >= 4.5
    page.mouse.move(0, 0)
    assert contrast(page, "#toggle-stream") >= 4.5
    page.locator('[data-mode="5"]').click()
    screenshot_dir = os.environ.get("PREVIEW_SCREENSHOT_DIR")
    if screenshot_dir:
        destination = Path(screenshot_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(destination / f"preview-{viewport['width']}.png"), full_page=True)
        if viewport["width"] == 1440:
            for mode_id in [1, 2, 3, 4, 5, 6, 9]:
                page.locator(f'[data-mode="{mode_id}"]').click()
                page.locator(".chart-shell").screenshot(
                    path=str(destination / f"mode-{mode_id}.png")
                )
    assert not errors
    assert page.evaluate("window.forbiddenCalls") == []
    assert set(requests) == {
        preview_url + suffix
        for suffix in (
            "",
            "styles.css",
            "fixtures.js",
            "demo.js",
            "fonts/atkinson-hyperlegible-next.woff2",
            "fonts/atkinson-hyperlegible-mono.woff2",
        )
    }
    context.close()


def test_reduced_motion_shows_full_fixture_without_playback(browser, preview_url):
    from playwright.sync_api import expect

    page = browser.new_page(reduced_motion="reduce")
    page.goto(preview_url)
    page.get_by_role("button", name="Start simulated stream").click()
    expect(page.locator("#stream-status")).to_contain_text("Full fixture shown with reduced motion")
    assert page.evaluate("state.visiblePoints === 121 && state.timer === null && !state.running")
    assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
    page.emulate_media(reduced_motion="no-preference")
    page.get_by_role("button", name="Start simulated stream").click()
    page.emulate_media(reduced_motion="reduce")
    expect(page.locator("#stream-status")).to_contain_text("Full fixture shown with reduced motion")
    assert page.evaluate("state.visiblePoints === 121 && state.timer === null && !state.running")
    page.close()


@pytest.mark.parametrize("width", [1440, 390])
def test_frame_panel_encodes_the_current_sample_and_keys_keep_their_names(
    browser, preview_url, width
):
    from playwright.sync_api import expect

    page = browser.new_page(viewport={"width": width, "height": 900})
    page.goto(preview_url)
    for mode_id, name in [(1, "Acceleration"), (5, "Temperature & humidity"), (9, "Analog input")]:
        expect(page.get_by_role("button", name=f"{mode_id} {name}")).to_have_attribute(
            "data-mode", str(mode_id)
        )
    for mode_id, wire_scale, file in [
        (4, 10, "pressure_plot_v1-2.phyphox"),
        (5, 1, "temperature_plot_v1-2.phyphox"),
    ]:
        page.locator(f'[data-mode="{mode_id}"]').click()
        values = page.evaluate(f"fixtures.get({mode_id}).series.map(s => s[120])")
        channels = [24.0] + [value / wire_scale for value in values]
        channels += [float("nan")] * (5 - len(channels))
        expected = [struct.pack("<f", value).hex(" ") for value in channels]
        shown = [
            " ".join(field.locator(".frame-bytes span").all_text_contents())
            for field in page.locator("#frame-fields li").all()
        ]
        assert shown == expected
        assert shown[-1] == "00 00 c0 7f"
        link = page.locator("#experiment-link")
        expect(link).to_have_text(file)
        assert link.get_attribute("href").endswith(f"/experiments/{file}")
    page.locator("#toggle-stream").click()
    expect(page.locator("#chart-pens .playhead")).to_have_count(1)
    page.locator("#reset-fixture").click()
    expect(page.locator("#chart-pens .playhead")).to_have_count(0)
    page.close()
