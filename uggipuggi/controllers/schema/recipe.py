# -*- coding: utf-8 -*-

from __future__ import absolute_import
import colander
import decimal
from uggipuggi.constants import TWEET_CHAR_LENGTH
from uggipuggi.controllers.schema.common import Images, Tags, Ingredients,\
     RecipeSteps, IngredientsQuant

class RecipeSchema(colander.MappingSchema):
    # timestamp ?
    recipe_name  = colander.SchemaNode(colander.String())
    user_id      = colander.SchemaNode(colander.String())
    user_name    = colander.SchemaNode(colander.String())
    steps = RecipeSteps()
    likes_count  = colander.SchemaNode(colander.Int())
    ingredients        = Ingredients()
    ingredients_quant  = IngredientsQuant()
    ingredients_metric = Ingredients()
    
    expose_level     = colander.SchemaNode(colander.Int())    
    ingredients_imgs = Ingredients()
    ingredients_ids  = Ingredients()
    tips = Tags()    
    description = colander.SchemaNode(colander.String(), missing='', validator=colander.Length(max=TWEET_CHAR_LENGTH))
    images = Images()
    tags = Tags()
    category = colander.SchemaNode(colander.String()) 
    rating_count = colander.SchemaNode(colander.Int())
    shares_count = colander.SchemaNode(colander.Int())    
    rating_total = colander.SchemaNode(colander.Int())
    prep_time    = colander.SchemaNode(colander.Int())
    cook_time    = colander.SchemaNode(colander.Int())
    #last_modified = DateTimeField(required=False)
    #comments     = ListField(EmbeddedDocumentField(Comment), required=False)
 
class Recipes(colander.SequenceSchema):
    recipe = RecipeSchema()
    
class RecipeCreateSchema(RecipeSchema):
    recipes = Recipes()    