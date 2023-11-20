from typing import TypeVar, List, Callable, Type

import msgspec
from memproxy import ItemCodec, Item, new_multi_get_filler

from init_app import get_pipeline

T = TypeVar('T')
K = TypeVar('K')


def new_codec(cls: Type[T]) -> ItemCodec[T]:
    json_encoder = msgspec.msgpack.Encoder()
    decoder = msgspec.msgpack.Decoder(cls)
    return ItemCodec(
        encode=json_encoder.encode,
        decode=decoder.decode,
    )


def new_cache_item(
        cls: Type[T],
        fill_func: Callable[[List[K]], List[T]],
        get_key: Callable[[T], K],
        default: T,
        key_name: Callable[[K], str],
) -> Callable[[], Item[T, K]]:
    codec = new_codec(cls)

    def new_func():
        filler = new_multi_get_filler(
            fill_func=fill_func, get_key_func=get_key,
            default=default,
        )
        return Item(
            pipe=get_pipeline(),
            key_fn=key_name,
            filler=filler,
            codec=codec
        )

    return new_func
