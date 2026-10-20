from datetime import datetime
from pydantic import BaseModel,ConfigDict,EmailStr,Field,field_validator
class Signup(BaseModel):
 email:EmailStr; password:str=Field(min_length=12,max_length=128); full_name:str|None=Field(default=None,max_length=120)
 @field_validator("full_name")
 @classmethod
 def clean_name(cls,v):return v.strip() or None if v else None
class Login(BaseModel):email:EmailStr;password:str=Field(min_length=1,max_length=128)
class UserOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int;email:EmailStr;full_name:str|None;email_verified:bool;created_at:datetime
class AuthOut(BaseModel):access_token:str;token_type:str="bearer";expires_in:int;user:UserOut
class Message(BaseModel):message:str
