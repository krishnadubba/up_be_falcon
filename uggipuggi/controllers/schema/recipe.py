# -*- coding: utf-8 -*-

from __future__ import absolute_import
import colander
import decimal
from uggipuggi.constants import TWEET_CHAR_LENGTH
from uggipuggi.controllers.schema.common import Images, Tags, Ingredients, RecipeSteps, IngredientsQuant

class RecipeSchema(colander.MappingSchema):
    # timestamp ?
    name = colander.SchemaNode(colander.String())
    #author = colander.SchemaNode(colander.String())
    prep_time = colander.SchemaNode(colander.Int())
    cook_time = colander.SchemaNode(colander.Int())
    description = colander.SchemaNode(colander.String(), missing='', validator=colander.Length(max=TWEET_CHAR_LENGTH))
    images = Images()
    tags = Tags()
    ingredients = Ingredients()
    ingredients_quant = IngredientsQuant()
    ingredients_metric = Ingredients()
    steps = RecipeSteps()
    category = colander.SchemaNode(colander.String()) 
    
class Recipes(colander.SequenceSchema):
    recipe = RecipeSchema()
    
class RecipeCreateSchema(RecipeSchema):
    recipes = Recipes()    