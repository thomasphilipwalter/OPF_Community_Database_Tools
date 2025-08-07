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

        // RFP Upload functionality
        this.setupRfpUpload();
    }

    setupTabHandling() {
        // Handle tab switching to ensure results are shown in the correct tab
        const keywordSearchTab = document.getElementById('keyword-search-tab');
        const rfpAnalysisTab = document.getElementById('rfp-analysis-tab');
        // When switching to RFP Analysis tab, hide any existing results
        rfpAnalysisTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
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

    setupRfpUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('rfpFile');
        const uploadForm = document.getElementById('rfpUploadForm');
        const analyzeBtn = document.getElementById('analyzeBtn');

        // File input change handler
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Drag and drop handlers
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // Form submit handler
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeRfp();
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            alert('Please select a PDF, DOC, or DOCX file.');
            return;
        }

        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            alert('File size must be less than 10MB.');
            return;
        }

        // Update UI
        this.updateFilePreview(file);
        document.getElementById('analyzeBtn').disabled = false;
    }

    updateFilePreview(file) {
        const uploadArea = document.getElementById('uploadArea');
        const filePreview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        // Update file info
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        // Show preview
        filePreview.style.display = 'block';
        uploadArea.classList.add('has-file');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async analyzeRfp() {
        const fileInput = document.getElementById('rfpFile');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const extractKeywords = document.getElementById('extractKeywords').checked;
        const findExperts = document.getElementById('findExperts').checked;

        if (!fileInput.files[0]) {
            alert('Please select a file first.');
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';

        try {
            const formData = new FormData();
            formData.append('rfp_file', fileInput.files[0]);
            formData.append('extract_keywords', extractKeywords);
            formData.append('find_experts', findExperts);

            const response = await fetch('/analyze-rfp', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.displayAnalysisResults(result);
            } else {
                alert('Analysis failed: ' + result.error);
            }
        } catch (error) {
            console.error('Error analyzing RFP:', error);
            alert('An error occurred while analyzing the RFP. Please try again.');
        } finally {
            // Reset button
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-search me-2"></i>Analyze RFP';
        }
    }

    displayAnalysisResults(result) {
        const analysisResults = document.getElementById('analysisResults');
        const analysisContent = document.getElementById('analysisContent');

        let content = '';

        if (result.keywords && result.keywords.length > 0) {
            content += `
                <div class="mb-4">
                    <h6><i class="fas fa-key me-2"></i>Key Requirements Identified</h6>
                    <div class="d-flex flex-wrap gap-2">
                        ${result.keywords.map(keyword => 
                            `<span class="badge bg-primary">${keyword}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        if (result.experts && result.experts.length > 0) {
            content += `
                <div class="mb-4">
                    <h6><i class="fas fa-users me-2"></i>Matching Experts (${result.experts.length} found)</h6>
                    <div class="row">
                        ${result.experts.map(expert => `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-title">${expert.first_name} ${expert.last_name}</h6>
                                        <p class="card-text text-muted">${expert.current_job || 'N/A'}</p>
                                        <p class="card-text"><small>${expert.current_company || 'N/A'}</small></p>
                                        <div class="d-flex flex-wrap gap-1">
                                            ${expert.matched_skills ? expert.matched_skills.map(skill => 
                                                `<span class="badge bg-success">${skill}</span>`
                                            ).join('') : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (!result.keywords && !result.experts) {
            content = '<p class="text-muted">No specific requirements or matching experts found. Try uploading a different document or adjusting the analysis options.</p>';
        }

        analysisContent.innerHTML = content;
        analysisResults.style.display = 'block';
    }
}

// Global function to remove uploaded file
function removeFile() {
    const fileInput = document.getElementById('rfpFile');
    const uploadArea = document.getElementById('uploadArea');
    const filePreview = document.getElementById('filePreview');
    const analyzeBtn = document.getElementById('analyzeBtn');

    // Clear file input
    fileInput.value = '';
    
    // Hide preview
    filePreview.style.display = 'none';
    
    // Reset upload area
    uploadArea.classList.remove('has-file');
    
    // Disable analyze button
    analyzeBtn.disabled = true;
}

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
    window.databaseSearchApp = new DatabaseSearchApp();
}); 