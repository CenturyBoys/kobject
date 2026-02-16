"""Thread safety tests for Kobject resolver registration."""

import threading

from kobject import Kobject


def test_concurrent_decoder_resolver_registration():
    """Ensure decoder resolver registration is thread-safe."""
    errors: list[Exception] = []

    def register_resolver(i: int) -> None:
        try:
            Kobject.set_decoder_resolver(int, lambda t, v, idx=i: v + idx)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=register_resolver, args=(i,)) for i in range(100)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors occurred during concurrent registration: {errors}"


def test_concurrent_encoder_resolver_registration():
    """Ensure encoder resolver registration is thread-safe."""
    errors: list[Exception] = []

    def register_resolver(i: int) -> None:
        try:
            Kobject.set_encoder_resolver(int, lambda v, idx=i: v + idx)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=register_resolver, args=(i,)) for i in range(100)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors occurred during concurrent registration: {errors}"


def test_concurrent_mixed_resolver_registration():
    """Ensure mixed decoder and encoder resolver registration is thread-safe."""
    errors: list[Exception] = []

    def register_decoder(i: int) -> None:
        try:
            Kobject.set_decoder_resolver(str, lambda t, v, idx=i: f"{v}_{idx}")
        except Exception as e:
            errors.append(e)

    def register_encoder(i: int) -> None:
        try:
            Kobject.set_encoder_resolver(str, lambda v, idx=i: f"{v}_{idx}")
        except Exception as e:
            errors.append(e)

    threads = []
    for i in range(50):
        threads.append(threading.Thread(target=register_decoder, args=(i,)))
        threads.append(threading.Thread(target=register_encoder, args=(i,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors occurred during concurrent registration: {errors}"
