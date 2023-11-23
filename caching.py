from typing import TypeVar, List, Callable, Type

import msgspec
from memproxy import ItemCodec, Item, new_multi_get_filler

from init_app import get_pipeline, add_item_stats

T = TypeVar('T')
K = TypeVar('K')


def new_codec(cls: Type[T]) -> ItemCodec[T]:
    encoder = msgspec.msgpack.Encoder()
    decoder = msgspec.msgpack.Decoder(cls)
    return ItemCodec(
        encode=encoder.encode,
        decode=decoder.decode,
    )


def new_cache_item(
        cls: Type[T],
        fill_func: Callable[[List[K]], List[T]],
        get_key: Callable[[T], K],
        default: Callable[[], T],
        key_name: Callable[[K], str],
) -> Callable[[], Item[T, K]]:
    codec = new_codec(cls)

    def new_func() -> Item[T, K]:
        filler = new_multi_get_filler(
            fill_func=fill_func, get_key_func=get_key,
            default=default(),
        )
        it = Item(
            pipe=get_pipeline(),
            key_fn=key_name,
            filler=filler,
            codec=codec
        )
        add_item_stats(cls.__name__, it)
        return it

    return new_func
