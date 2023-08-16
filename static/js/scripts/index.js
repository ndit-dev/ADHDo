//
// Listener to update the order of categories and tasks after drag and drop action
//
document.addEventListener('DOMContentLoaded', function() {
	var categoriesContainer = document.getElementById('categories-container');
		Sortable.create(categoriesContainer, {
			filter: '.toggle-arrow',
			onUpdate: function (evt) {
				var newOrder = {};
				Array.from(evt.from.children).forEach((category, index) => {
					var categoryId = category.getAttribute('data-category-id');
					newOrder[categoryId] = index;
				});
				
				fetch('/update_category_order', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({ order: newOrder })
				});
			},
			// other options here for categories
		});

	var taskContainers = document.querySelectorAll('.tasks');
	taskContainers.forEach(function(container) {
		Sortable.create(container, {
			// filter delete button here if needed,
			onUpdate: function (evt) {
				var newOrder = {};
				Array.from(evt.from.children).forEach((task, index) => {
					var taskId = task.getAttribute('data-task-id');
					newOrder[taskId] = index;
				});
				
				fetch('/update_task_order', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({ order: newOrder })
				});
			},
			// other options here
		});
	});
});

//
// play a sound when a check box is checked
//
window.onload = function() {
	var checkboxes = document.querySelectorAll('.task-complete-checkbox');
	checkboxes.forEach(function(checkbox) {
		checkbox.addEventListener('change', function(event) {
		console.log('Checkbox change detected'); // Debugging message

		// Prevent the default form submission
		event.preventDefault();
		
		// Play the sound
		if (this.checked) {
			document.getElementById('completeSound').play();
		}

		// Get the task ID from the data-task-id attribute
		var taskId = this.dataset.taskId;

		// Send an AJAX request to update the task on the server
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/complete_task/' + taskId); // Replace with your URL
		xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		xhr.send('completed=' + (this.checked ? 'true' : 'false'));
		
		// Handle the response from the server
		xhr.onreadystatechange = function() {
			if (xhr.readyState == 4 && xhr.status == 200) {
			console.log('Server response received:', xhr.responseText); // Debugging message
			}
		};

		console.log('AJAX request sent'); // Debugging message
		});
	});
};

//
// collapse and contract tasks under categories
//
function toggleTasks(element, category_id) {
	var arrow = element; // element itself is the toggle-arrow span
	var category = element.parentElement.parentElement.parentElement; // Find the parent category div
	var tasks = category.querySelector('.tasks');
	
	// Toggle the display of the tasks
	if (tasks.style.display === 'none' || tasks.style.display === '') {
		tasks.style.display = 'block';
		arrow.innerHTML = '⤴'; // Change arrow direction
	} else {
		tasks.style.display = 'none';
		arrow.innerHTML = '⤵'; // Change arrow direction
	}

	// Send an AJAX request to update the category's visibility in the database
	var xhr = new XMLHttpRequest();
	xhr.open('POST', '/toggle_category/' + category_id);
	xhr.onreadystatechange = function() {
		if (xhr.readyState == 4 && xhr.status == 200) {
			// Handle server response if needed
		}
	};
	xhr.send();
}

//
// Delete tasks without page reload
//
document.getElementById('categories-container').addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-task-icon')) {
        var taskId = e.target.getAttribute('data-task-id');

        // Confirm deletion
        if (!window.confirm("Are you sure you want to delete this task?")) {
            return;
        }

        // Send an AJAX request to delete the task
        fetch('/delete_task/' + taskId, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.category_deleted) {
                // Remove the entire category div if the server indicates that the category was deleted
                var categoryDiv = e.target.closest('.category');
                categoryDiv.remove();
            } else {
                // Otherwise, just remove the task
                var taskDiv = e.target.closest('.task');
                taskDiv.remove();
            }
        })
        .catch(error => {
            console.error('Failed to delete task', error);
        });
    }
});


//
// add tasks and categories on the fly and without page reload
//
function renderTask(task) {
	var completedCheck = task.completed ? 'checked' : '';
	return `
		<div class="task" data-task-id="${task.id}">
			<input type="checkbox" class="task-complete-checkbox" name="completed" value="true" data-task-id="${task.id}" ${completedCheck}>
			<strong>${task.title}</strong>
			<i class="fas fa-times delete-task-icon" data-task-id="${task.id}"></i>
		</div>`;
}

function renderCategory(category, taskHtml) {
	var isVisible = category.is_visible ? 'display:block' : 'display:none';
	return `
		<div class="category" data-category-id="${category.id}">
			<div class="category-title">
				<h3>
					${category.name}
					<span class="toggle-arrow" onclick="toggleTasks(this, ${category.id})">
						${category.is_visible ? '⤴' : '⤵'}
					</span>
				</h3>
			</div>
			<div class="tasks" id="tasks-for-category-${category.id}" style="${isVisible};">
				${taskHtml}
			</div>
		</div>`;
}

window.addEventListener('DOMContentLoaded', (event) => {
	var showAddTaskButton = document.getElementById('show-add-task');
	var addTaskForm = document.getElementById('add-task-form');
	var taskTitleInput = document.getElementById('task-title');

	showAddTaskButton.addEventListener('click', function() {
		if(addTaskForm.style.display === 'none' || addTaskForm.style.display === '') {
			addTaskForm.style.display = 'block';
			taskTitleInput.focus(); // Focus the task title input
		} else {
			addTaskForm.style.display = 'none'; // Hide the form
		}
	});
		
	document.getElementById('add-task-form-inner').addEventListener('submit', function(e) {
		e.preventDefault(); // Prevent normal form submission

		// Construct the form data
		var formData = new FormData(this);

		// Send the data via AJAX
		fetch('/add_task', {
			method: 'POST',
			body: formData
		})
		.then(response => response.json())
		.then(data => {
			if (data.status === 'success') {
				addTaskForm.style.display = 'none'; // Hide the form
				showAddTaskButton.style.display = 'block'; // Show the plus sign button

				// Reset the form
				this.reset();

				var categoriesContainer = document.getElementById('categories-container');

				// Render the new task as HTML
				var newTaskHtml = renderTask(data.task);

				// Check if the category already exists on the page
				var taskListId = 'tasks-for-category-' + data.category_id;
				var taskList = document.getElementById(taskListId);

				if (taskList) {
					// Append the new task to the existing category's task list
					taskList.insertAdjacentHTML('beforeend', newTaskHtml);
				} else {
					// Render the new category and task
					var newCategoryHtml = renderCategory(data.category, newTaskHtml);

					// Append the new category to the categories container
					categoriesContainer.insertAdjacentHTML('beforeend', newCategoryHtml);
				}
			}
		});
	});
});