from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .database import Base

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='employee')
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    first_name = Column(String)
    last_name = Column(String)
    position = Column(String)
    department = Column(String)
    phone = Column(String)
    
    organization = relationship("Organization", back_populates="users")
    assignments = relationship("Assignment", secondary="user_assignments", back_populates="users")
    submissions = relationship("Submission", back_populates="employee")
    managed_teams = relationship("Team", back_populates="manager")
    teams = relationship("Team", secondary="team_members", back_populates="members")


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    manager_id = Column(Integer, ForeignKey('users.id'))

    organization = relationship("Organization", back_populates="teams")
    manager = relationship("User", back_populates="managed_teams")
    members = relationship("User", secondary="team_members", back_populates="teams")
    assignments = relationship("Assignment", back_populates="team")

class TeamMember(Base):
    __tablename__ = 'team_members'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), primary_key=True)

class Assignment(Base):
    __tablename__ = 'assignments'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    is_general = Column(Boolean, default=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="assignments")
    users = relationship("User", secondary="user_assignments", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class UserAssignment(Base):
    __tablename__ = 'user_assignments'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), primary_key=True)

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    employee_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')
    graded_by = Column(Integer, ForeignKey('users.id'))
    graded_at = Column(DateTime)

    assignment = relationship("Assignment", back_populates="submissions")
    employee = relationship("User", back_populates="submissions")


class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    is_group_chat = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationParticipant(Base):
    __tablename__ = 'conversation_participants'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), primary_key=True)
    last_read_timestamp = Column(DateTime)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False)

class MessageReadStatus(Base):
    __tablename__ = 'message_read_status'
    message_id = Column(Integer, ForeignKey('messages.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
