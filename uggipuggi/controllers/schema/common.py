# -*- coding: utf-8 -*-

from __future__ import absolute_import
import colander

class Images(colander.SequenceSchema):
    image = colander.SchemaNode(colander.String(), validator=colander.url)

class Ingredients(colander.SequenceSchema):
    ingredient = colander.SchemaNode(colander.String())

class IngredientsQuant(colander.SequenceSchema):
    ingredient_quant = colander.SchemaNode(colander.Float())
    
class RecipeSteps(colander.SequenceSchema):
    step = colander.SchemaNode(colander.String())
    
class Tags(colander.SequenceSchema):
    tag = colander.SchemaNode(colander.String())

