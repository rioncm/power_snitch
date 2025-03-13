# Power Snitch Development Rules

## Core Principles

### 1. Application Authority
- Power Snitch is the primary application on the system
- Runs with root privileges
- Responsible for managing all system-level configurations
- Must push settings to other services (NUT, iptables, etc.)
- No assumption of other applications being present

### 2. Code Philosophy
- **KISS (Keep It Simple, Stupid)**
  - Avoid complex solutions
  - Prefer straightforward implementations
  - Minimize dependencies
  - Use simple, clear code structures

- **DRY (Don't Repeat Yourself)**
  - Centralize common functionality
  - Create reusable components
  - Maintain single sources of truth
  - Avoid code duplication

- **Modularity**
  - Clear separation of concerns
  - Independent components
  - Easy to test and maintain
  - Well-defined interfaces

### 3. Logging Standards
- **DEBUG Level**
  - Detailed operational information
  - Step-by-step process tracking
  - Variable values and state changes
  - Verbose logging for troubleshooting

- **INFO Level**
  - Moderate operational updates
  - Important state changes
  - Configuration updates
  - Service status changes

- **ERROR Level**
  - Operation failures
  - Service issues
  - Configuration problems
  - Connection failures

- **CRITICAL Level**
  - System-level failures
  - Security breaches
  - Data corruption
  - Service crashes

### 4. Security Guidelines
- Implement basic security practices
- No advanced security requirements
- Focus on essential protections
- Secure credential storage
- Basic access controls

## Technical Requirements

### 1. Platform Constraints
- Target: Raspberry Pi Zero W
- OS: Reapian/Debian minimal install
- Limited resources
- USB connectivity for UPS

### 2. Stack Requirements
- SQLite database
- Shell scripts for system operations
- Python with standard libraries
- Flask (HTTP only)
- OS-level Python package installation

### 3. Configuration Management
- Centralized configuration in database
- System service configuration management
- Configuration validation
- Error handling for misconfigurations

### 4. Service Integration
- NUT configuration management
- iptables/iptables-persistent management
- Web interface for all operations
- Notification service management

## Development Guidelines

### 1. Code Organization
- Clear file structure
- Logical module grouping
- Consistent naming conventions
- Comprehensive documentation

### 2. Error Handling
- Graceful degradation
- Clear error messages
- Proper logging
- Recovery procedures

### 3. Testing Requirements
- Unit tests for components
- Integration tests for services
- System-level testing
- Error scenario testing

### 4. Documentation
- Code comments
- API documentation
- Configuration guides
- Troubleshooting guides

## Implementation Rules

### 1. Database Operations
- Use SQLAlchemy ORM
- Proper session management
- Transaction handling
- Error recovery

### 2. System Operations
- Shell script execution
- Service management
- Configuration file handling
- Permission management

### 3. Web Interface
- Simple, functional design
- Clear user feedback
- Error message display
- Status indicators

### 4. Notification Services
- Configurable alert methods
- Error handling
- Retry mechanisms
- Status tracking

## Maintenance Rules

### 1. Code Updates
- Version control
- Change documentation
- Testing requirements
- Deployment procedures

### 2. Logging Management
- Log rotation
- Size management
- Cleanup procedures
- Archive policies

### 3. Configuration Changes
- Validation requirements
- Backup procedures
- Rollback plans
- Update notifications

### 4. System Monitoring
- Resource usage
- Service status
- Error tracking
- Performance metrics

## Deployment Rules

### 1. Installation
- Simple installation process
- Dependency management
- Configuration setup
- Service initialization

### 2. Updates
- Non-disruptive updates
- Configuration preservation
- Service management
- Rollback capability

### 3. Backup
- Database backups
- Configuration backups
- Log backups
- Recovery procedures

### 4. Monitoring
- Service status
- Resource usage
- Error tracking
- Performance monitoring 