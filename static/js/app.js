// OPFA Community Database Search Application

class DatabaseSearchApp {
    constructor() {
        this.currentResults = [];
        this.currentKeyword = '';
        // Track applied filters (not just selected checkboxes)
        this.appliedSourceFilters = [];
        this.appliedExperienceFilters = [];
        this.appliedSustainabilityExperienceFilters = [];
        this.appliedCompetenciesFilters = [];
        this.appliedSectorsFilters = [];
        this.init();
    }

    init() {
        this.loadStats();
        this.setupEventListeners();
        this.setupTabHandling();
    }

    setupEventListeners() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearBtn');
        const exportBtn = document.getElementById('exportBtn');

        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        clearBtn.addEventListener('click', () => {
            this.clearResults();
        });

        exportBtn.addEventListener('click', () => {
            this.exportResults();
        });

        // Enter key support
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch();
            }
        });

        // RFP functionality removed
    }

    setupTabHandling() {
        // Handle tab switching to ensure results are shown in the correct tab
        const keywordSearchTab = document.getElementById('keyword-search-tab');
        const rfpAnalysisTab = document.getElementById('rfp-analysis-tab');
        
        // When switching to RFP Analysis tab, hide any existing results and load RFP list
        rfpAnalysisTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
            this.loadRfpList();
        });

        // When switching back to Keyword Search tab, show results if they exist
        keywordSearchTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (this.currentResults.length > 0 && resultsContainer.style.display === 'none') {
                resultsContainer.style.display = 'block';
            }
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            if (stats.error) {
                console.error('Error loading stats:', stats.error);
                return;
            }

            const statsDisplay = document.getElementById('stats-display');
            statsDisplay.innerHTML = `
                <div>${stats.total_records} Total Records</div>
                <div>${stats.records_with_linkedins} With LinkedIn</div>
                <div>${stats.records_with_resumes} With Resumes</div>
            `;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const keyword = searchInput.value.trim();

        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    keyword,
                    source_filters: this.appliedSourceFilters,
                    experience_filters: this.appliedExperienceFilters,
                    sustainability_experience_filters: this.appliedSustainabilityExperienceFilters,
                    competencies_filters: this.appliedCompetenciesFilters,
                    sectors_filters: this.appliedSectorsFilters
                })
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.currentResults = data.results;
            this.currentKeyword = data.keyword;
            this.displayResults(data);

        } catch (error) {
            this.showError('An error occurred while searching. Please try again.');
            console.error('Search error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    getSelectedSourceFilters() {
        const sourceFilters = [];
        const sourceCheckboxes = document.querySelectorAll('.source-checkboxes input[type="checkbox"]:checked');
        
        sourceCheckboxes.forEach(checkbox => {
            sourceFilters.push(checkbox.value);
        });
        
        return sourceFilters;
    }

    getSelectedExperienceFilters() {
        const experienceFilters = [];
        const experienceCheckboxes = document.querySelectorAll('.experience-checkboxes input[type="checkbox"]:checked');
        
        experienceCheckboxes.forEach(checkbox => {
            experienceFilters.push(checkbox.value);
        });
        
        return experienceFilters;
    }

    getSelectedSustainabilityExperienceFilters() {
        const sustainabilityExperienceFilters = [];
        const sustainabilityExperienceCheckboxes = document.querySelectorAll('.sustainability-experience-checkboxes input[type="checkbox"]:checked');
        
        sustainabilityExperienceCheckboxes.forEach(checkbox => {
            sustainabilityExperienceFilters.push(checkbox.value);
        });
        
        return sustainabilityExperienceFilters;
    }

    getSelectedCompetenciesFilters() {
        const competenciesFilters = [];
        const competenciesCheckboxes = document.querySelectorAll('.competencies-checkboxes input[type="checkbox"]:checked');
        
        competenciesCheckboxes.forEach(checkbox => {
            competenciesFilters.push(checkbox.value);
        });
        
        return competenciesFilters;
    }

    getSelectedSectorsFilters() {
        const sectorsFilters = [];
        const sectorsCheckboxes = document.querySelectorAll('.sectors-checkboxes input[type="checkbox"]:checked');
        
        sectorsCheckboxes.forEach(checkbox => {
            sectorsFilters.push(checkbox.value);
        });
        
        return sectorsFilters;
    }

    displayResults(data) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsTitle = document.getElementById('resultsTitle');
        const resultsList = document.getElementById('resultsList');

        // Update title
        const count = data.count;
        const keyword = data.keyword;
        const keywordText = keyword ? ` for "${keyword}"` : '';
        resultsTitle.innerHTML = `
            <i class="fas fa-search me-2"></i>
            <span style="font-family: 'Inter Tight', sans-serif; font-weight: 400;">Found ${count} result${count !== 1 ? 's' : ''}${keywordText}</span>
        `;

        // Clear previous results
        resultsList.innerHTML = '';

        if (count === 0) {
            resultsList.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle me-2"></i>
                        No results found for "${keyword}". Try a different keyword or phrase.
                    </div>
                </div>
            `;
        } else {
            // Display results in cards
            data.results.forEach((result, index) => {
                const card = this.createResultCard(result, keyword);
                resultsList.appendChild(card);
            });
        }

        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    createResultCard(result, keyword) {
        const template = document.getElementById('resultCardTemplate');
        const card = template.content.cloneNode(true);

        // Set person name
        const personName = card.querySelector('.person-name');
        const firstName = result.first_name || '';
        const lastName = result.last_name || '';
        const fullName = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        
        // Make the name clickable if email exists
        if (result.email) {
            personName.innerHTML = `<a href="/user/${encodeURIComponent(result.email)}" target="_blank" style="color: inherit; text-decoration: none;">${this.highlightKeyword(fullName, keyword)}</a>`;
        } else {
            personName.innerHTML = this.highlightKeyword(fullName, keyword);
        }

        // Set location
        const location = card.querySelector('.location');
        const city = result.city || '';
        const country = result.country || '';
        const locationText = [city, country].filter(Boolean).join(', ') || 'Location not specified';
        location.textContent = locationText;

        // Add fields to card body
        const fieldsContainer = card.querySelector('.result-fields');
        this.addFieldsToCard(fieldsContainer, result, keyword);

        return card;
    }

    addFieldsToCard(container, result, keyword) {
        const fieldMappings = {
            'email': { label: 'Email', icon: 'fas fa-envelope', type: 'email' },
            'email_other': { label: 'Other Email', icon: 'fas fa-envelope', type: 'email' },
            'linkedin': { label: 'LinkedIn', icon: 'fab fa-linkedin', type: 'link' },
            'current_job': { label: 'Current Job', icon: 'fas fa-briefcase' },
            'current_company': { label: 'Current Company', icon: 'fas fa-building' },
            'linkedin_summary': { label: 'LinkedIn Summary', icon: 'fas fa-file-alt' },
            'resume': { label: 'Resume', icon: 'fas fa-file-pdf', type: 'text' },
            'years_xp': { label: 'Years Experience', icon: 'fas fa-clock' },
            'years_sustainability_xp': { label: 'Sustainability Experience', icon: 'fas fa-leaf' },
            'linkedin_skills': { label: 'LinkedIn Skills', icon: 'fas fa-tools' },
            'key_competencies': { label: 'Key Competencies', icon: 'fas fa-star' },
            'key_sectors': { label: 'Key Sectors', icon: 'fas fa-industry' },
            'executive_summary': { label: 'Executive Summary', icon: 'fas fa-user-tie' },
            'gender_identity': { label: 'Gender Identity', icon: 'fas fa-user' },
            'race_ethnicity': { label: 'Race/Ethnicity', icon: 'fas fa-users' },
            'lgbtqia': { label: 'LGBTQIA+', icon: 'fas fa-heart' },
            'source': { label: 'Source', icon: 'fas fa-info-circle' }
        };

        // Add fields in order
        Object.entries(fieldMappings).forEach(([fieldName, config]) => {
            const value = result[fieldName];
            if (value && value.trim()) {
                const fieldGroup = this.createFieldGroup(config.label, value, config.icon, config.type, keyword);
                container.appendChild(fieldGroup);
            }
        });
    }

    createFieldGroup(label, value, icon, type = 'text', keyword = '') {
        const fieldGroup = document.createElement('div');
        fieldGroup.className = 'field-group';

        const fieldLabel = document.createElement('div');
        fieldLabel.className = 'field-label';
        fieldLabel.innerHTML = `<i class="${icon} field-icon"></i>${label}`;

        const fieldValue = document.createElement('div');
        fieldValue.className = 'field-value';

        if (type === 'email') {
            fieldValue.innerHTML = `<a href="mailto:${value}" target="_blank">${this.highlightKeyword(value, keyword)}</a>`;
        } else if (type === 'link') {
            fieldValue.innerHTML = `<a href="${value}" target="_blank">${this.highlightKeyword(value, keyword)}</a>`;
        } else if (label.toLowerCase().includes('resume')) {
            // Enhanced resume display with better formatting
            const resumeId = 'resume-' + Math.random().toString(36).substr(2, 9);
            const formattedResume = this.formatResumeText(value);
            fieldValue.innerHTML = `
                <div class="resume-toggle">
                    <button class="btn btn-sm btn-outline-secondary" onclick="toggleResume('${resumeId}')">
                        <i class="fas fa-eye me-1"></i>View Resume
                    </button>
                    <div id="${resumeId}" class="resume-content" style="display: none;">
                        <div class="resume-text">
                            ${this.highlightKeyword(formattedResume, keyword)}
                        </div>
                    </div>
                </div>
            `;
        } else if (label.toLowerCase().includes('skills') || label.toLowerCase().includes('competencies') || label.toLowerCase().includes('sectors')) {
            // Handle skills/competencies as tags
            const skills = value.split(',').map(skill => skill.trim()).filter(Boolean);
            const skillsHtml = skills.map(skill => 
                `<span class="skill-tag">${this.highlightKeyword(skill, keyword)}</span>`
            ).join('');
            fieldValue.innerHTML = `<div class="skills-tags">${skillsHtml}</div>`;
        } else {
            fieldValue.innerHTML = this.highlightKeyword(value, keyword);
        }

        fieldGroup.appendChild(fieldLabel);
        fieldGroup.appendChild(fieldValue);

        return fieldGroup;
    }

    formatResumeText(text) {
        if (!text) return '';
        
        // Preserve line breaks and formatting
        let formattedText = text
            // Preserve line breaks
            .replace(/\n/g, '<br>')
            // Preserve multiple spaces (for indentation)
            .replace(/  /g, '&nbsp;&nbsp;')
            // Make headers bold (lines that end with ** or are in ALL CAPS)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Make section headers stand out (lines that are mostly uppercase)
            .replace(/^([A-Z\s]{3,}):?$/gm, '<h6 class="resume-section">$1</h6>')
            // Make bullet points more visible
            .replace(/^[\s]*•[\s]*(.*)$/gm, '<div class="resume-bullet">• $1</div>')
            .replace(/^[\s]*[-*][\s]*(.*)$/gm, '<div class="resume-bullet">• $1</div>')
            // Make numbered lists
            .replace(/^[\s]*(\d+\.)[\s]*(.*)$/gm, '<div class="resume-numbered">$1 $2</div>')
            // Highlight contact information
            .replace(/([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})/g, '<span class="resume-email">$1</span>')
            .replace(/(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})/g, '<span class="resume-phone">$1</span>')
            // Make LinkedIn URLs clickable
            .replace(/(linkedin\.com\/in\/[^\s]+)/g, '<a href="https://$1" target="_blank" class="resume-link">$1</a>')
            // Make URLs clickable
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="resume-link">$1</a>')
            // Preserve bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Preserve italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        return formattedText;
    }

    highlightKeyword(text, keywords) {
        if (!keywords || !text) return text;
        
        // Split keywords by comma and clean them
        const keywordList = keywords.split(',').map(kw => kw.trim()).filter(kw => kw);
        
        if (keywordList.length === 0) return text;
        
        let highlightedText = text;
        
        // Highlight each keyword with a different color
        keywordList.forEach((keyword, index) => {
            const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const colorClass = index === 0 ? 'highlight' : `highlight-${index + 1}`;
            highlightedText = highlightedText.replace(regex, `<span class="${colorClass}">$1</span>`);
        });
        
        return highlightedText;
    }

    clearResults() {
        const resultsContainer = document.getElementById('resultsContainer');
        const searchInput = document.getElementById('searchInput');
        
        resultsContainer.style.display = 'none';
        searchInput.value = '';
        this.currentResults = [];
        this.currentKeyword = '';
        
        searchInput.focus();
    }

    exportResults() {
        if (!this.currentResults.length) {
            this.showError('No results to export');
            return;
        }

        // Create CSV content
        const headers = Object.keys(this.currentResults[0]);
        const csvContent = [
            headers.join(','),
            ...this.currentResults.map(result => 
                headers.map(header => {
                    const value = result[header] || '';
                    // Escape commas and quotes in CSV
                    return `"${value.replace(/"/g, '""')}"`;
                }).join(',')
            )
        ].join('\n');

        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `opfa_search_results_${this.currentKeyword}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const searchBtn = document.querySelector('#searchForm button[type="submit"]');
        
        if (show) {
            loadingSpinner.style.display = 'block';
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
        } else {
            loadingSpinner.style.display = 'none';
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Search';
        }
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth' });
    }

    hideError() {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.style.display = 'none';
    }

    // RFP functionality
    async loadRfpList() {
        try {
            const response = await fetch('/api/rfp-list');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading RFP list:', data.error);
                return;
            }

            this.displayRfpList(data.rfps);
        } catch (error) {
            console.error('Error loading RFP list:', error);
        }
    }

    displayRfpList(rfps) {
        const rfpList = document.getElementById('rfpList');
        const noRfpsMessage = document.getElementById('noRfpsMessage');
        
        if (rfps.length === 0) {
            rfpList.style.display = 'none';
            noRfpsMessage.style.display = 'block';
            return;
        }

        rfpList.style.display = 'block';
        noRfpsMessage.style.display = 'none';
        
        rfpList.innerHTML = '';
        
        rfps.forEach(rfp => {
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item list-group-item-action';
            listItem.onclick = () => this.selectRfp(rfp);
            
            const dueDate = rfp.due_date ? new Date(rfp.due_date).toLocaleDateString() : 'No due date';
            const isOverdue = rfp.due_date && new Date(rfp.due_date) < new Date();
            
            listItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${this.escapeHtml(rfp.project_name)}</h6>
                        <small class="text-muted">${this.escapeHtml(rfp.organization_group)}</small>
                        <br>
                        <small class="text-muted">
                            <i class="fas fa-map-marker-alt me-1"></i>${this.escapeHtml(rfp.country)} • ${this.escapeHtml(rfp.region)}
                        </small>
                    </div>
                    <div class="text-end">
                        <small class="text-muted">${dueDate}</small>
                        ${isOverdue ? '<br><span class="badge bg-danger">Overdue</span>' : ''}
                    </div>
                </div>
            `;
            
            rfpList.appendChild(listItem);
        });
    }

    selectRfp(rfp) {
        // Remove active class from all items
        document.querySelectorAll('#rfpList .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected item
        event.target.closest('.list-group-item').classList.add('active');
        
        // Display RFP details
        this.displayRfpDetails(rfp);
    }

    displayRfpDetails(rfp) {
        const rfpDetails = document.getElementById('rfpDetails');
        const dueDate = rfp.due_date ? new Date(rfp.due_date).toLocaleDateString() : 'Not specified';
        const isOverdue = rfp.due_date && new Date(rfp.due_date) < new Date();
        
        rfpDetails.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h4>${this.escapeHtml(rfp.project_name)}</h4>
                    <p class="text-muted mb-3">${this.escapeHtml(rfp.organization_group)}</p>
                    
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <strong>Country:</strong> ${this.escapeHtml(rfp.country)}
                        </div>
                        <div class="col-md-6">
                            <strong>Region:</strong> ${this.escapeHtml(rfp.region)}
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <strong>Industry:</strong> ${this.escapeHtml(rfp.industry)}
                        </div>
                        <div class="col-md-6">
                            <strong>Due Date:</strong> 
                            <span class="${isOverdue ? 'text-danger' : ''}">${dueDate}</span>
                            ${isOverdue ? ' <span class="badge bg-danger">Overdue</span>' : ''}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 text-end">
                    <button class="btn btn-primary mb-2" onclick="app.uploadDocument(${rfp.id})">
                        <i class="fas fa-upload me-2"></i>Upload Document
                    </button>
                    <br>
                    <button class="btn btn-outline-secondary btn-sm" onclick="app.editRfp(${rfp.id})">
                        <i class="fas fa-edit me-1"></i>Edit
                    </button>
                </div>
            </div>
        `;
    }

    showAddRfpModal() {
        console.log('Add RFP button clicked!');
        // TODO: Implement add RFP modal
        alert('Add RFP functionality coming soon!');
    }

    uploadDocument(rfpId) {
        // TODO: Implement document upload
        alert('Document upload functionality coming soon!');
    }

    editRfp(rfpId) {
        // TODO: Implement edit RFP
        alert('Edit RFP functionality coming soon!');
    }
}

// RFP functionality removed

// Global function for toggling resume content
function toggleResume(resumeId) {
    const resumeContent = document.getElementById(resumeId);
    const button = resumeContent.previousElementSibling;
    const icon = button.querySelector('i');
    
    if (resumeContent.style.display === 'none') {
        resumeContent.style.display = 'block';
        icon.className = 'fas fa-eye-slash me-1';
        button.innerHTML = '<i class="fas fa-eye-slash me-1"></i>Hide Resume';
    } else {
        resumeContent.style.display = 'none';
        icon.className = 'fas fa-eye me-1';
        button.innerHTML = '<i class="fas fa-eye me-1"></i>View Resume';
    }
}

// Global function for toggling filter options
function toggleFilter() {
    const filterOptions = document.getElementById('filterOptions');
    const filterBtn = document.getElementById('filterBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const icon = filterBtn.querySelector('i');
    
    if (filterOptions.style.display === 'none') {
        filterOptions.style.display = 'block';
        icon.className = 'fas fa-filter me-1';
        filterBtn.innerHTML = '<i class="fas fa-filter me-1"></i>Hide Filters';
        // Hide clear filters button when opening filter box
        clearFiltersBtn.style.display = 'none';
    } else {
        filterOptions.style.display = 'none';
        icon.className = 'fas fa-filter me-1';
        filterBtn.innerHTML = '<i class="fas fa-filter me-1"></i>Filters';
    }
}

// Global function for applying filters
function applyFilters() {
    // Close the filter box
    const filterOptions = document.getElementById('filterOptions');
    const filterBtn = document.getElementById('filterBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const icon = filterBtn.querySelector('i');
    
    filterOptions.style.display = 'none';
    icon.className = 'fas fa-filter me-1';
    filterBtn.innerHTML = '<i class="fas fa-filter me-1"></i>Filters';
    
    // Store the current checkbox states as applied filters
    if (window.databaseSearchApp) {
        window.databaseSearchApp.appliedSourceFilters = getSelectedSourceFiltersGlobal();
        window.databaseSearchApp.appliedExperienceFilters = getSelectedExperienceFiltersGlobal();
        window.databaseSearchApp.appliedSustainabilityExperienceFilters = getSelectedSustainabilityExperienceFiltersGlobal();
        window.databaseSearchApp.appliedCompetenciesFilters = getSelectedCompetenciesFiltersGlobal();
        window.databaseSearchApp.appliedSectorsFilters = getSelectedSectorsFiltersGlobal();
    }
    
    // Show clear filters button if any filters are selected
    const selectedSourceFilters = getSelectedSourceFiltersGlobal();
    const selectedExperienceFilters = getSelectedExperienceFiltersGlobal();
    const selectedSustainabilityExperienceFilters = getSelectedSustainabilityExperienceFiltersGlobal();
    const selectedCompetenciesFilters = getSelectedCompetenciesFiltersGlobal();
    const selectedSectorsFilters = getSelectedSectorsFiltersGlobal();
    if (selectedSourceFilters.length > 0 || selectedExperienceFilters.length > 0 || selectedSustainabilityExperienceFilters.length > 0 || selectedCompetenciesFilters.length > 0 || selectedSectorsFilters.length > 0) {
        clearFiltersBtn.style.display = 'inline-block';
    }
}

// Global function to get selected source filters
function getSelectedSourceFiltersGlobal() {
    const sourceFilters = [];
    const sourceCheckboxes = document.querySelectorAll('.source-checkboxes input[type="checkbox"]:checked');
    
    sourceCheckboxes.forEach(checkbox => {
        sourceFilters.push(checkbox.value);
    });
    
    return sourceFilters;
}

// Global function to get selected experience filters
function getSelectedExperienceFiltersGlobal() {
    const experienceFilters = [];
    const experienceCheckboxes = document.querySelectorAll('.experience-checkboxes input[type="checkbox"]:checked');
    
    experienceCheckboxes.forEach(checkbox => {
        experienceFilters.push(checkbox.value);
    });
    
    return experienceFilters;
}

// Global function to get selected sustainability experience filters
function getSelectedSustainabilityExperienceFiltersGlobal() {
    const sustainabilityExperienceFilters = [];
    const sustainabilityExperienceCheckboxes = document.querySelectorAll('.sustainability-experience-checkboxes input[type="checkbox"]:checked');
    
    sustainabilityExperienceCheckboxes.forEach(checkbox => {
        sustainabilityExperienceFilters.push(checkbox.value);
    });
    
    return sustainabilityExperienceFilters;
}

// Global function to get selected competencies filters
function getSelectedCompetenciesFiltersGlobal() {
    const competenciesFilters = [];
    const competenciesCheckboxes = document.querySelectorAll('.competencies-checkboxes input[type="checkbox"]:checked');
    
    competenciesCheckboxes.forEach(checkbox => {
        competenciesFilters.push(checkbox.value);
    });
    
    return competenciesFilters;
}

// Global function to get selected sectors filters
function getSelectedSectorsFiltersGlobal() {
    const sectorsFilters = [];
    const sectorsCheckboxes = document.querySelectorAll('.sectors-checkboxes input[type="checkbox"]:checked');
    
    sectorsCheckboxes.forEach(checkbox => {
        sectorsFilters.push(checkbox.value);
    });
    
    return sectorsFilters;
}

// Global function for clearing filters
function clearFilters() {
    // Uncheck all source checkboxes
    const sourceCheckboxes = document.querySelectorAll('.source-checkboxes input[type="checkbox"]');
    sourceCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Uncheck all experience checkboxes
    const experienceCheckboxes = document.querySelectorAll('.experience-checkboxes input[type="checkbox"]');
    experienceCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Uncheck all sustainability experience checkboxes
    const sustainabilityExperienceCheckboxes = document.querySelectorAll('.sustainability-experience-checkboxes input[type="checkbox"]');
    sustainabilityExperienceCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Uncheck all competencies checkboxes
    const competenciesCheckboxes = document.querySelectorAll('.competencies-checkboxes input[type="checkbox"]');
    competenciesCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Uncheck all sectors checkboxes
    const sectorsCheckboxes = document.querySelectorAll('.sectors-checkboxes input[type="checkbox"]');
    sectorsCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Clear applied filters in the app instance
    if (window.databaseSearchApp) {
        window.databaseSearchApp.appliedSourceFilters = [];
        window.databaseSearchApp.appliedExperienceFilters = [];
        window.databaseSearchApp.appliedSustainabilityExperienceFilters = [];
        window.databaseSearchApp.appliedCompetenciesFilters = [];
        window.databaseSearchApp.appliedSectorsFilters = [];
    }
    
    // Hide clear filters button
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    clearFiltersBtn.style.display = 'none';
}



// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DatabaseSearchApp();
    window.databaseSearchApp = window.app; // Keep backward compatibility
}); 