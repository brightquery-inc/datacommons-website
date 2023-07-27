# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from server.config.subject_page_pb2 import SubjectPageConfig
from server.lib.nl.config_builder import base
from server.lib.nl.config_builder import builder
import server.lib.nl.detection.types as dtypes
import server.lib.nl.fulfillment.context as ctx
import server.lib.nl.fulfillment.types as ftypes

# Helper class to build chart config for Insights


class Builder:

  def __init__(self, state: ftypes.PopulateState, env_config: builder.Config,
               sv2thing: base.SV2Thing):
    self.uttr = state.uttr
    self.page_config = SubjectPageConfig()
    self.env_config = env_config
    self.sv2thing = sv2thing

    self.is_place_comparison = False
    if len(state.uttr.places) > 1:
      if ctx.classifications_of_type_from_utterance(
          state.uttr, dtypes.ClassificationType.COMPARISON):
        self.is_place_comparison = True

    self.is_var_comparison = False
    if len(state.uttr.svs) > 1:
      if ctx.classifications_of_type_from_utterance(
          state.uttr, dtypes.ClassificationType.CORRELATION):
        self.is_var_comparison = True

    metadata = self.page_config.metadata
    main_place = state.uttr.places[0]
    metadata.place_dcid.append(main_place.dcid)
    if state.place_type:
      metadata.contained_place_types[main_place.place_type] = \
        state.place_type.value

    self.category = None
    self.block = None
    self.column = None

  def nopc(self):
    return self.env_config.nopc_vars

  def new_category(self, title, dcid):
    self.category = self.page_config.categories.add()
    self.category.title = title
    if dcid:
      self.category.dcid = dcid

  def new_block(self, title, description=''):
    self.block = self.category.blocks.add()
    self.block.title = base.decorate_block_title(title=title)
    if description:
      self.block.description = description

  def new_column(self):
    self.column = self.block.columns.add()
    return self.column

  def update_sv_spec(self, stat_var_spec_map):
    for sv_key, spec in stat_var_spec_map.items():
      self.category.stat_var_spec[sv_key].CopyFrom(spec)

  # 1. If there are duplicate charts, drops the subsequent tiles.
  # 2. As a result of the dedupe if any column, block or category
  #    is empty, deletes it.
  # 3. Finally, if there is a singleton block in a category and both
  #    the block and category have names, drop the block name.
  def cleanup_config(self):
    # From inside to out, delete duplicate charts and cleanup
    # any empties.
    chart_keys = set()
    out_cats = []
    for cat in self.page_config.categories:
      out_blks = []
      for blk in cat.blocks:
        out_cols = []
        for col in blk.columns:
          out_tiles = []
          for tile in col.tiles:
            x = tile.SerializeToString()
            if x not in chart_keys:
              out_tiles.append(tile)
            chart_keys.add(x)
          del col.tiles[:]
          if out_tiles:
            col.tiles.extend(out_tiles)
            out_cols.append(col)
        del blk.columns[:]
        if out_cols:
          blk.columns.extend(out_cols)
          out_blks.append(blk)
      del cat.blocks[:]
      if out_blks:
        cat.blocks.extend(out_blks)
        out_cats.append(cat)
    del self.page_config.categories[:]
    if out_cats:
      self.page_config.categories.extend(out_cats)

    for cat in self.page_config.categories:
      if len(cat.blocks) == 1 and cat.title and cat.blocks[0].title:
        # Note: Category title will be topic name and block title
        # will be SVPG.  The latter is better curated, so for now
        # use that.
        # TODO: Revisit after topic names are better.
        cat.title = cat.blocks[0].title
        cat.blocks[0].title = ''
