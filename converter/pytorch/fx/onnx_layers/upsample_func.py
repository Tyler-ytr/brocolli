from loguru import logger
from onnx import helper
from onnx import TensorProto as tp
import numpy as np

from onnx_layers.base_layer import BaseLayer


class UpsampleFunc(BaseLayer):
    def __init__(self, source_node, module=None, auto_gen=True):
        super(UpsampleFunc, self).__init__(source_node, module, auto_gen)

    def generate_node(self, name=None, params=None, attr_dict=None):
        scale_factor = self._source_node.kwargs['scale_factor']

        if scale_factor is None:
            size = self._source_node.kwargs['size']

            if isinstance(size, int):
                dim = len(self._source_node.meta['tensor_meta'].shape)
                output_size = self._source_node.meta['tensor_meta'].shape
                input_size = self._source_node.args[0].meta['tensor_meta'].shape
                size = [size] * dim

            scales = [1. if i < 2 else
                      float(output_size[-(dim - i)]) / float(input_size[-(dim - i)])
                      for i in range(0, dim)]
        else:
            if isinstance(scale_factor, float):
                dim = self._source_node.meta['tensor_meta'].shape[2:]
                scale_factor = [scale_factor] * len(dim)

            scales = [1, 1] +  scale_factor      
            
        scales = np.array(scales)
        self.create_params(self._name + "_roi", np.array([]), tp.FLOAT)
        self.create_params(self._name + "_scale", scales, tp.FLOAT)
        node = helper.make_node(
            "Resize", self._in_names, self._out_names, self._name, mode="nearest"
        )
        logger.info("upsample_layer: " + self._name + " created")
        self._node.append(node)