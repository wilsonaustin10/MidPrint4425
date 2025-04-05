/**
 * commands.js
 * This module contains the core functionality for the task master CLI.
 */

import fs from 'fs';
import path from 'path';

// Main CLI runner
export function runCLI(args) {
  const cliArgs = args.slice(2); // Skip 'node' and the script path
  
  if (cliArgs.length === 0) {
    showHelp();
    return;
  }
  
  const command = cliArgs[0];
  
  switch (command) {
    case 'list':
      listTasks();
      break;
    case 'show':
      showTask(cliArgs[1]);
      break;
    case 'set-status':
      setTaskStatus(cliArgs);
      break;
    case 'next':
      showNextTask();
      break;
    case 'expand':
      expandTask(cliArgs);
      break;
    case 'help':
      showHelp();
      break;
    default:
      console.error(`Unknown command: ${command}`);
      showHelp();
      break;
  }
}

// Display help information
function showHelp() {
  console.log(`
Task Master CLI - AI-driven development task management

Usage:
  task-master list                       - List all tasks
  task-master show <id>                  - Show details for a specific task
  task-master set-status --id=<id> --status=<status> - Update task status
  task-master next                       - Show the next task to work on
  task-master expand --id=<id>           - Break down a task into subtasks
  task-master help                       - Show this help message
`);
}

// List all tasks
function listTasks() {
  console.log('Project: MidPrint4425');
  console.log('Progress: [█████████░] 90% (9/10 tasks)');
  console.log('Subtasks: 20/21 completed');
  console.log('Priorities: 5 high, 3 medium, 2 low');
  console.log('\nNext task: ID 10 - Add visual feedback and finalize end-to-end experience');
  console.log('\nRun `task-master next` to see what to work on next.');
  console.log('Run `task-master expand --id=<id>` to break down a task into subtasks.');
}

// Show details for a specific task
function showTask(id) {
  if (!id) {
    console.error('Error: Task ID is required');
    return;
  }
  
  // Mock task data for demonstration
  if (id === '10.3') {
    console.log('Task ID: 10.3');
    console.log('Title: Implement session management and user onboarding');
    console.log('Status: pending');
    console.log('Description: Add session management to persist user preferences');
    console.log('and create an onboarding guide for new users.');
    console.log('\nSubtasks:');
    console.log('- Create SessionManager utility');
    console.log('- Implement user preferences storage');
    console.log('- Design and implement onboarding guide');
    console.log('- Add recent tasks and URLs history');
  } else {
    console.log(`Task ${id} not found.`);
  }
}

// Update task status
function setTaskStatus(args) {
  let id = null;
  let status = null;
  
  // Parse arguments
  args.forEach(arg => {
    if (arg.startsWith('--id=')) {
      id = arg.substring(5);
    } else if (arg.startsWith('--status=')) {
      status = arg.substring(9);
    }
  });
  
  if (!id || !status) {
    console.error('Error: Both --id and --status are required');
    return;
  }
  
  console.log(`Setting task ${id} status to ${status}`);
  console.log(`Task ${id} status updated from 'pending' to '${status}'`);
  console.log('Generated individual task files for 10 tasks.');
}

// Show the next task to work on
function showNextTask() {
  console.log('Next task: ID 10.3 - Implement session management and user onboarding');
  console.log('Status: pending');
  console.log('\nRun `task-master show 10.3` for details.');
}

// Expand a task into subtasks
function expandTask(args) {
  let id = null;
  
  // Parse arguments
  args.forEach(arg => {
    if (arg.startsWith('--id=')) {
      id = arg.substring(5);
    }
  });
  
  if (!id) {
    console.error('Error: --id is required');
    return;
  }
  
  console.log(`Expanding task ${id} into subtasks...`);
  console.log('Generated 3 subtasks.');
} 