import os

import numpy as np
import pytest
import torch
from pydantic import parse_obj_as

from docarray import BaseDoc
from docarray.typing.bytes.audio_bytes import AudioBytes
from docarray.typing.tensor.audio.audio_ndarray import AudioNdArray
from docarray.typing.tensor.audio.audio_torch_tensor import AudioTorchTensor
from docarray.utils._internal.misc import is_tf_available

tf_available = is_tf_available()
if tf_available:
    import tensorflow as tf
    import tensorflow._api.v2.experimental.numpy as tnp

    from docarray.typing.tensor.audio import AudioTensorFlowTensor


@pytest.mark.parametrize(
    'tensor,cls_audio_tensor,cls_tensor',
    [
        (torch.zeros(1000, 2), AudioTorchTensor, torch.Tensor),
        (np.zeros((1000, 2)), AudioNdArray, np.ndarray),
    ],
)
def test_set_audio_tensor(tensor, cls_audio_tensor, cls_tensor):
    class MyAudioDoc(BaseDoc):
        tensor: cls_audio_tensor

    doc = MyAudioDoc(tensor=tensor)
    assert isinstance(doc.tensor, cls_audio_tensor)
    assert isinstance(doc.tensor, cls_tensor)
    assert (doc.tensor == tensor).all()


@pytest.mark.tensorflow
def test_set_audio_tensorflow_tensor():
    class MyAudioDoc(BaseDoc):
        tensor: AudioTensorFlowTensor

    doc = MyAudioDoc(tensor=tf.zeros((1000, 2)))
    assert isinstance(doc.tensor, AudioTensorFlowTensor)
    assert isinstance(doc.tensor.tensor, tf.Tensor)
    assert tnp.allclose(doc.tensor.tensor, tf.zeros((1000, 2)))


@pytest.mark.parametrize(
    'cls_tensor,tensor',
    [
        (AudioNdArray, np.zeros((1000, 2))),
        (AudioTorchTensor, torch.zeros(1000, 2)),
        (AudioTorchTensor, np.zeros((1000, 2))),
    ],
)
def test_validation(cls_tensor, tensor):
    arr = parse_obj_as(cls_tensor, tensor)
    assert isinstance(arr, cls_tensor)


@pytest.mark.tensorflow
def test_validation_tensorflow():
    arr = parse_obj_as(AudioTensorFlowTensor, tf.zeros((1000, 2)))
    assert isinstance(arr, AudioTensorFlowTensor)


@pytest.mark.parametrize(
    'cls_tensor,tensor',
    [
        (AudioNdArray, torch.zeros(1000, 2)),
        (AudioNdArray, 'hello'),
        (AudioTorchTensor, 'hello'),
    ],
)
def test_illegal_validation(cls_tensor, tensor):
    match = str(cls_tensor).split('.')[-1][:-2]
    with pytest.raises(ValueError, match=match):
        parse_obj_as(cls_tensor, tensor)


@pytest.mark.proto
@pytest.mark.parametrize(
    'cls_tensor,tensor,proto_key',
    [
        (AudioTorchTensor, torch.zeros(1000, 2), AudioTorchTensor._proto_type_name),
        (AudioNdArray, np.zeros((1000, 2)), AudioNdArray._proto_type_name),
    ],
)
def test_proto_tensor(cls_tensor, tensor, proto_key):
    tensor = parse_obj_as(cls_tensor, tensor)
    proto = tensor._to_node_protobuf()
    assert proto_key in str(proto)


@pytest.mark.tensorflow
def test_proto_tensor_tensorflow():
    tensor = parse_obj_as(AudioTensorFlowTensor, tf.zeros((1000, 2)))
    proto = tensor._to_node_protobuf()
    assert AudioTensorFlowTensor._proto_type_name in str(proto)


@pytest.mark.parametrize(
    'cls_tensor,tensor',
    [
        (AudioTorchTensor, torch.zeros(1000, 2)),
        (AudioNdArray, np.zeros((1000, 2))),
    ],
)
def test_save_audio_tensor_to_wav_file(cls_tensor, tensor, tmpdir):
    tmp_file = str(tmpdir / 'tmp.wav')
    audio_tensor = parse_obj_as(cls_tensor, tensor)
    audio_tensor.save(tmp_file)
    assert os.path.isfile(tmp_file)


@pytest.mark.tensorflow
def test_save_audio_tensorflow_tensor_to_wav_file(tmpdir):
    tmp_file = str(tmpdir / 'tmp.wav')
    audio_tensor = parse_obj_as(AudioTensorFlowTensor, tf.zeros((1000, 2)))
    audio_tensor.save(tmp_file)
    assert os.path.isfile(tmp_file)


@pytest.mark.parametrize(
    'audio_tensor',
    [
        parse_obj_as(AudioTorchTensor, torch.zeros(1000, 2)),
        parse_obj_as(AudioNdArray, np.zeros((1000, 2))),
    ],
)
def test_save_audio_tensor_to_bytes(audio_tensor):
    b = audio_tensor.to_bytes()
    isinstance(b, bytes)
    isinstance(b, AudioBytes)
