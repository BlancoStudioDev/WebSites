document.addEventListener('DOMContentLoaded', function() {
    // Store all program data
    let allPrograms = {};
    
    // Get DOM elements
    const loaderContainer = document.getElementById('loader-container');
    const errorMessage = document.getElementById('error-message');
    const channelsGrid = document.getElementById('channels-grid');
    const emptyResults = document.getElementById('empty-results');
    const searchInput = document.getElementById('search-input');
    const timeFilter = document.getElementById('time-filter');
    const channelFilter = document.getElementById('channel-filter');
    const currentTimeElement = document.getElementById('current-time');
    const lastUpdatedElement = document.getElementById('last-updated');
    
    // Auto-refresh variables
    let refreshIntervalId = null;
    let secondsUntilRefresh = 0;
    let lastRefreshTimestamp = null;
    let searchTimeout = null;
    
    // Update current time
    function updateCurrentTime() {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            day: 'numeric', 
            month: 'long', 
            hour: '2-digit', 
            minute: '2-digit' 
        };
        const timeString = now.toLocaleString('it-IT', options);
        currentTimeElement.textContent = timeString;
    }
    
    // Initial time update
    updateCurrentTime();
    
    // Update time every minute
    setInterval(updateCurrentTime, 60000);
    
    // Update last refreshed timestamp
    function updateLastRefreshed() {
        const now = new Date();
        lastRefreshTimestamp = now;
        const timeString = now.toLocaleString('it-IT', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        lastUpdatedElement.textContent = timeString;
    }
    
    // Channel colors - more vibrant and modern
    const channelColors = [
        { bg: '#3a86ff', color: '#ffffff' }, // Blue
        { bg: '#ff006e', color: '#ffffff' }, // Pink
        { bg: '#8338ec', color: '#ffffff' }, // Purple
        { bg: '#fb5607', color: '#ffffff' }, // Orange
        { bg: '#06d6a0', color: '#ffffff' }, // Teal
        { bg: '#ffbe0b', color: '#000000' }, // Yellow
        { bg: '#3a0ca3', color: '#ffffff' }, // Deep Purple
        { bg: '#f15bb5', color: '#ffffff' }, // Light Pink
        { bg: '#118ab2', color: '#ffffff' }, // Ocean Blue
        { bg: '#ef476f', color: '#ffffff' }, // Red
        { bg: '#04724d', color: '#ffffff' }, // Dark Green
        { bg: '#495057', color: '#ffffff' }  // Dark Gray
    ];
    
    // Fetch TV schedule data from the JSON file
    function fetchTVSchedules() {
        // Show loader and hide error message
        loaderContainer.style.display = 'flex';
        errorMessage.style.display = 'none';
        channelsGrid.style.display = 'none';
        emptyResults.style.display = 'none';
        
        // Add cache-busting query parameter to prevent browser caching
        const cacheBuster = new Date().getTime();
        const url = `output/all_tv_schedules.json?_=${cacheBuster}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load data');
                }
                return response.json();
            })
            .then(data => {
                // Store the data
                allPrograms = data;
                
                // Hide loader
                loaderContainer.style.display = 'none';
                
                // Update timestamp
                updateLastRefreshed();
                
                // Populate channel filter to ensure it's up to date
                populateChannelFilter(Object.keys(allPrograms));
                
                // Display the data (applying current filters)
                filterSchedules();
            })
            .catch(error => {
                console.error('Error loading data:', error);
                loaderContainer.style.display = 'none';
                errorMessage.style.display = 'flex';
            });
    }
    
    // Initial data fetch
    fetchTVSchedules();
    
    // Populate channel filter dropdown
    function populateChannelFilter(channels) {
        // Save the current selection if there is one
        const currentSelection = channelFilter.value;
        
        // Clear existing options except the "All Channels" option
        while (channelFilter.options.length > 1) {
            channelFilter.remove(1);
        }
        
        // Sort channels alphabetically
        channels.sort().forEach(channel => {
            const option = document.createElement('option');
            option.value = channel;
            option.textContent = channel;
            channelFilter.appendChild(option);
        });
        
        // Restore previous selection if it still exists, otherwise default to "all"
        if (currentSelection && Array.from(channelFilter.options).some(opt => opt.value === currentSelection)) {
            channelFilter.value = currentSelection;
        } else {
            channelFilter.value = 'all';
        }
    }
    
    // Check if a program is currently airing
    function isNowPlaying(programTime) {
        const [hours, minutes] = programTime.split(':').map(Number);
        const programTimeValue = hours * 60 + minutes;
        
        const now = new Date();
        const currentHour = now.getHours();
        const currentMinute = now.getMinutes();
        const currentTimeValue = currentHour * 60 + currentMinute;
        
        // Consider a program as "now playing" if it started within the last 60 minutes
        return (currentTimeValue >= programTimeValue) && 
               (currentTimeValue <= programTimeValue + 60);
    }
    
    // Format search matches to highlight matching text
    function highlightMatch(text, searchTerm) {
        if (!searchTerm) return text;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    // Display schedules
    function displaySchedules(schedules) {
        // Clear existing content
        channelsGrid.innerHTML = '';
        
        // Check if any schedules to display
        if (Object.keys(schedules).length === 0) {
            emptyResults.style.display = 'flex';
            channelsGrid.style.display = 'none';
            return;
        }
        
        // Show grid, hide empty message
        channelsGrid.style.display = 'grid';
        emptyResults.style.display = 'none';
        
        // Get search term for highlighting
        const searchTerm = searchInput.value.trim();
        
        // Sort channels alphabetically
        const sortedChannels = Object.keys(schedules).sort();
        
        // Create a card for each channel
        sortedChannels.forEach((channel, index) => {
            const programs = schedules[channel];
            
            // Skip channels with no programs
            if (!programs || programs.length === 0) return;
            
            // Get color for this channel (cycle through the array)
            const colorIndex = index % channelColors.length;
            const colorScheme = channelColors[colorIndex];
            
            // Create channel card
            const channelCard = document.createElement('div');
            channelCard.className = 'channel-card';
            channelCard.dataset.channel = channel;
            
            // Create header with channel name
            const header = document.createElement('div');
            header.className = 'channel-header';
            header.style.backgroundColor = colorScheme.bg;
            header.style.color = colorScheme.color;
            
            // Channel name and logo
            const channelName = document.createElement('span');
            channelName.textContent = channel;
            
            const channelLogo = document.createElement('div');
            channelLogo.className = 'channel-logo';
            const logoIcon = document.createElement('i');
            logoIcon.className = 'fas fa-broadcast-tower';
            logoIcon.style.fontSize = '14px';
            channelLogo.appendChild(logoIcon);
            
            header.appendChild(channelName);
            header.appendChild(channelLogo);
            
            // Create content div for programs
            const content = document.createElement('div');
            content.className = 'channel-content';
            
            // Add programs to content
            programs.forEach(program => {
                const programDiv = document.createElement('div');
                programDiv.className = 'program';
                
                // Check if this program is currently airing
                if (isNowPlaying(program.time)) {
                    programDiv.classList.add('now-playing');
                }
                
                programDiv.dataset.time = program.time;
                programDiv.dataset.title = program.title.toLowerCase();
                
                const timeSpan = document.createElement('span');
                timeSpan.className = 'time';
                timeSpan.textContent = program.time;
                
                const titleSpan = document.createElement('span');
                titleSpan.className = 'title';
                
                // Highlight matches in title if searching
                if (searchTerm) {
                    titleSpan.innerHTML = highlightMatch(program.title, searchTerm);
                } else {
                    titleSpan.textContent = program.title;
                }
                
                programDiv.appendChild(timeSpan);
                programDiv.appendChild(titleSpan);
                content.appendChild(programDiv);
            });
            
            // Assemble the card
            channelCard.appendChild(header);
            channelCard.appendChild(content);
            channelsGrid.appendChild(channelCard);
        });
    }
    
    // Filter schedules based on search input and filters
    function filterSchedules() {
        // Check if data is loaded
        if (!allPrograms || Object.keys(allPrograms).length === 0) {
            return;
        }
        
        const searchTerm = searchInput.value.toLowerCase().trim();
        const timeFilterValue = timeFilter.value;
        const channelFilterValue = channelFilter.value;
        
        // Create a filtered copy of the data
        const filteredData = {};
        
        // Get current time for "on now" and "coming next" filters
        const now = new Date();
        const currentHour = now.getHours();
        const currentMinute = now.getMinutes();
        const currentTimeValue = currentHour * 60 + currentMinute;
        
        // Process each channel
        Object.keys(allPrograms).forEach(channel => {
            // Skip if not matching channel filter
            if (channelFilterValue !== 'all' && channel !== channelFilterValue) {
                return;
            }
            
            // Filter programs for this channel
            const filteredPrograms = allPrograms[channel].filter(program => {
                // Filter by search term
                const matchesSearch = searchTerm === '' || 
                                     program.title.toLowerCase().includes(searchTerm);
                
                if (!matchesSearch) return false;
                
                // Parse program time
                const [hours, minutes] = program.time.split(':').map(Number);
                const programTimeValue = hours * 60 + minutes;
                
                // Filter by time
                let matchesTime = true;
                
                switch (timeFilterValue) {
                    case 'all':
                        matchesTime = true;
                        break;
                    case 'now':
                        // Find programs that are on now (within 60 min window)
                        matchesTime = (currentTimeValue >= programTimeValue) && 
                                     (currentTimeValue <= programTimeValue + 60);
                        break;
                    case 'next':
                        // Find programs starting in the next 1-2 hours
                        matchesTime = (programTimeValue > currentTimeValue) && 
                                     (programTimeValue <= currentTimeValue + 120);
                        break;
                    case 'prime':
                        // Prime time (20:00 - 23:00)
                        matchesTime = hours >= 20 && hours < 23;
                        break;
                    case 'morning':
                        // Morning (06:00 - 12:00)
                        matchesTime = hours >= 6 && hours < 12;
                        break;
                    case 'afternoon':
                        // Afternoon (12:00 - 18:00)
                        matchesTime = hours >= 12 && hours < 18;
                        break;
                    case 'evening':
                        // Evening (18:00 - 00:00)
                        matchesTime = hours >= 18 && hours < 24;
                        break;
                    case 'night':
                        // Night (00:00 - 06:00)
                        matchesTime = hours >= 0 && hours < 6;
                        break;
                    default:
                        matchesTime = true;
                }
                
                return matchesTime;
            });
            
            // Only add channel to filtered data if it has matching programs
            if (filteredPrograms.length > 0) {
                filteredData[channel] = filteredPrograms;
            }
        });
        
        // Update display with filtered data
        displaySchedules(filteredData);
    }
    
    // Set up event listeners for search and filters with proper debouncing
    function setupEventListeners() {
        // Search input with debouncing
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterSchedules();
            }, 300);
        });
        
        // Time filter change
        timeFilter.addEventListener('change', function() {
            filterSchedules();
        });
        
        // Channel filter change
        channelFilter.addEventListener('change', function() {
            filterSchedules();
        });
        
        // Enter key in search box
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                clearTimeout(searchTimeout);
                filterSchedules();
            }
        });
    }
    
    // Initialize event listeners
    setupEventListeners();
    
    // Add responsiveness to channel grid
    function adjustGridLayout() {
        const container = document.querySelector('.container');
        if (!container) return;
        
        const containerWidth = container.offsetWidth;
        
        // Adjust number of columns based on container width
        if (containerWidth < 600) {
            channelsGrid.style.gridTemplateColumns = '1fr';
        } else if (containerWidth < 900) {
            channelsGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        } else {
            channelsGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
        }
    }
    
    // Call the layout adjustment on load and on window resize
    window.addEventListener('resize', adjustGridLayout);
    adjustGridLayout();
});