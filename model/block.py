from model.base import Base
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
class Block(Base):
    __tablename__ = 'block'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gallery_id = Column(Integer, ForeignKey('gallery.id'))
    index = Column(Integer)
    original = Column(Text)
    
    translation = Column(Text)
    ai_generate = Column(Text)
    
    gallery = relationship("Gallery", back_populates="blocks")