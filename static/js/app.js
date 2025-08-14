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
        this.currentRfps = []; // Store current RFP list
        this.selectedRfp = null; // Store currently selected RFP
        this.editingRfpId = null; // Store RFP ID being edited
        this.uploadingRfpId = null; // Store RFP ID for document upload
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

        // RFP form submission
        const saveRfpBtn = document.getElementById('saveRfpBtn');
        if (saveRfpBtn) {
            saveRfpBtn.addEventListener('click', () => {
                this.saveRfp();
            });
        }

        // RFP edit form submission
        const saveEditRfpBtn = document.getElementById('saveEditRfpBtn');
        if (saveEditRfpBtn) {
            saveEditRfpBtn.addEventListener('click', () => {
                this.saveEditRfp();
            });
        }

        // Document upload form submission
        const uploadDocumentBtn = document.getElementById('uploadDocumentBtn');
        if (uploadDocumentBtn) {
            uploadDocumentBtn.addEventListener('click', () => {
                this.uploadDocumentFile();
            });
        }
    }

    setupTabHandling() {
        // Handle tab switching to ensure results are shown in the correct tab
        const keywordSearchTab = document.getElementById('keyword-search-tab');
        const rfpAnalysisTab = document.getElementById('rfp-analysis-tab');
        const australianTendersTab = document.getElementById('australian-tenders-tab');
        const gizTendersTab = document.getElementById('giz-tenders-tab');
        const undpTendersTab = document.getElementById('undp-tenders-tab');
        
        // When switching to RFP Analysis tab, hide any existing results and load RFP list
        rfpAnalysisTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
            this.loadRfpList();
        });

        // When switching to Australian Tenders tab, load Australian tenders
        australianTendersTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
            this.loadTendersBySource('Australian Government Tenders');
        });

        // When switching to GIZ Tenders tab, load GIZ tenders
        gizTendersTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
            this.loadTendersBySource('GIZ (German Development Agency)');
        });

        // When switching to UNDP Tenders tab, load UNDP tenders
        undpTendersTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
            this.loadTendersBySource('UNDP (United Nations Development Programme)');
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
        if (!this.currentResults || !this.currentResults.length) {
            this.showError('No results to export');
            return;
        }

        // Define the fields we want to export in order
        const exportFields = [
            'first_name',
            'last_name', 
            'email',
            'email_other',
            'city',
            'country',
            'current_job',
            'current_company',
            'linkedin',
            'linkedin_summary',
            'years_xp',
            'years_sustainability_xp',
            'linkedin_skills',
            'key_competencies',
            'key_sectors',
            'executive_summary',
            'gender_identity',
            'race_ethnicity',
            'lgbtqia',
            'source'
        ];

        // Create headers
        const headers = [
            'First Name',
            'Last Name',
            'Email',
            'Other Email',
            'City',
            'Country',
            'Current Job',
            'Current Company',
            'LinkedIn',
            'LinkedIn Summary',
            'Years Experience',
            'Sustainability Experience',
            'LinkedIn Skills',
            'Key Competencies',
            'Key Sectors',
            'Executive Summary',
            'Gender Identity',
            'Race/Ethnicity',
            'LGBTQIA+',
            'Source'
        ];

        // Create CSV content
        const csvContent = [
            headers.join(','),
            ...this.currentResults.map(result => 
                exportFields.map(field => {
                    const value = result[field] || '';
                    // Clean the value - remove newlines and extra spaces
                    const cleanValue = value.toString().replace(/\n/g, ' ').replace(/\r/g, ' ').replace(/\s+/g, ' ').trim();
                    // Escape commas and quotes in CSV
                    return `"${cleanValue.replace(/"/g, '""')}"`;
                }).join(',')
            )
        ].join('\n');

        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `opfa_search_results_${this.currentKeyword || 'all'}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showSuccess(`Exported ${this.currentResults.length} results to CSV`);
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

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

            this.currentRfps = data.rfps; // Store RFPs in class
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
            listItem.onclick = (event) => this.selectRfp(rfp, event);
            
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
                        <br>
                        <button class="btn btn-outline-danger btn-sm mt-1" onclick="event.stopPropagation(); app.deleteRfp(${rfp.id}, '${this.escapeHtml(rfp.project_name)}')" title="Delete RFP">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            rfpList.appendChild(listItem);
        });
    }

    selectRfp(rfp, event = null) {
        // Remove active class from all items
        document.querySelectorAll('#rfpList .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected item (if event provided)
        if (event && event.target.closest('.list-group-item')) {
            event.target.closest('.list-group-item').classList.add('active');
        }
        
        // Store the selected RFP
        this.selectedRfp = rfp;
        
        // Display RFP details
        this.displayRfpDetails(rfp);
        
        // Load documents for this RFP
        this.loadDocuments(rfp.id);
    }

    displayRfpDetails(rfp) {
        const rfpDetails = document.getElementById('rfpDetails');
        const dueDate = rfp.due_date ? new Date(rfp.due_date).toLocaleDateString() : 'Not specified';
        const isOverdue = rfp.due_date && new Date(rfp.due_date) < new Date();
        const createdDate = rfp.created_at ? new Date(rfp.created_at).toLocaleDateString() : 'Unknown';
        const projectCost = rfp.project_cost ? `${rfp.currency || ''} ${rfp.project_cost}` : 'Not specified';
        
        rfpDetails.innerHTML = `
            <div class="row mb-3">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">${this.escapeHtml(rfp.project_name)}</h4>
                        <div>
                            <button class="btn btn-primary btn-sm me-2" onclick="app.uploadDocument(${rfp.id})" title="Upload Document">
                                <i class="fas fa-upload"></i>
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.editRfp(${rfp.id})" title="Edit RFP">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Metadata Section -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table" style="border-collapse: collapse; table-layout: fixed; width: 100%;">
                                    <thead>
                                        <tr>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Org. / Group</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Country</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Region</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Industry</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Project Focus</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">OPF Gap Size</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">OPF Gaps</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 12.5%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Due Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.organization_group ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.organization_group)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.country ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.country)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.region ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.region)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.industry ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.industry)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.project_focus ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.project_focus)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.opf_gap_size ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.opf_gap_size)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.opf_gaps ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.opf_gaps)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.due_date ? `<span class="${isOverdue ? 'text-danger' : 'text-muted'}" style="font-family: 'Azeret Mono', monospace;">${dueDate}</span>${isOverdue ? ' <span class="badge bg-danger">Overdue</span>' : ''}` : ''}</td>
                                        </tr>
                                    </tbody>
                                </table>
                                
                                <table class="table" style="border-collapse: collapse; table-layout: fixed; width: 100%;">
                                    <thead>
                                        <tr>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Project Cost</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Posting Contact</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Deliverables</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Potential Experts</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Specific Staffing Needs</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Link</th>
                                            <th style="border: 1px solid #dee2e6; padding: 8px; width: 14.28%; word-wrap: break-word; white-space: normal; background-color: #AFCFD0;">Uploaded At</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.project_cost ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${projectCost}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.posting_contact ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.posting_contact)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.deliverables ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.deliverables)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.potential_experts ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.potential_experts)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.specific_staffing_needs ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.specific_staffing_needs)}</span>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.link ? `<a href="${this.escapeHtml(rfp.link)}" target="_blank" class="text-primary" style="font-family: 'Azeret Mono', monospace;">${this.escapeHtml(rfp.link)}</a>` : ''}</td>
                                            <td style="border: 1px solid #dee2e6; padding: 8px; word-wrap: break-word; white-space: normal; vertical-align: top;">${rfp.created_at ? `<span class="text-muted" style="font-family: 'Azeret Mono', monospace;">${createdDate}</span>` : ''}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Document Management Section -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <div class="mb-3">
                                <h5 class="card-title mb-0">Document Management</h5>
                                <small class="text-muted">Upload and manage documents for this RFP project.</small>
                            </div>
                            <div id="documentsList">
                                <div class="text-center text-muted">
                                    <i class="fas fa-spinner fa-spin"></i>
                                    <p class="mt-2">Loading documents...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </div>
            
            <!-- AI Analysis Section -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <div class="mb-3">
                                <h5 class="card-title mb-0">AI Analysis</h5>
                                <small class="text-muted">Analyze uploaded documents using AI to extract insights and recommendations.</small>
                            </div>
                            <div id="aiAnalysisContent">
                                ${this.hasExistingAnalysis(rfp) ? this.displayExistingAnalysis(rfp) : `
                                    <div class="text-center">
                                        <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                                            <i class="fas fa-robot me-2"></i>Generate AI Analysis
                                        </button>
                                        <div class="mt-2">
                                            <button class="btn btn-outline-secondary btn-sm" onclick="app.initKnowledgeBase()">
                                                <i class="fas fa-database me-2"></i>Initialize Knowledge Base
                                            </button>
                                        </div>
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showAddRfpModal() {
        console.log('Add RFP button clicked!');
        // Clear the form
        document.getElementById('addRfpForm').reset();
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('addRfpModal'));
        modal.show();
    }

    uploadDocument(rfpId) {
        // Store the RFP ID for the upload
        this.uploadingRfpId = rfpId;
        
        // Clear the form
        document.getElementById('uploadDocumentForm').reset();
        document.getElementById('uploadProgress').style.display = 'none';
        
        // Show the modal
        const uploadModal = new bootstrap.Modal(document.getElementById('uploadDocumentModal'));
        uploadModal.show();
    }

    async uploadDocumentFile() {
        const fileInput = document.getElementById('documentFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a file to upload');
            return;
        }
        
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('File size must be less than 10MB');
            return;
        }
        
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please upload a PDF, DOC, or DOCX file');
            return;
        }
        
        // Show progress bar
        const progressBar = document.getElementById('uploadProgress');
        const progressBarInner = progressBar.querySelector('.progress-bar');
        progressBar.style.display = 'block';
        progressBarInner.style.width = '0%';
        progressBarInner.textContent = 'Uploading...';
        
        // Disable upload button
        const uploadBtn = document.getElementById('uploadDocumentBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
        
        try {
            const formData = new FormData();
            formData.append('document', file);
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                progressBarInner.style.width = progress + '%';
                if (progress >= 90) {
                    clearInterval(progressInterval);
                }
            }, 200);
            
            const response = await fetch(`/api/document-upload/${this.uploadingRfpId}`, {
                method: 'POST',
                body: formData
            });
            
            clearInterval(progressInterval);
            progressBarInner.style.width = '100%';
            progressBarInner.textContent = 'Complete!';
            
            const result = await response.json();
            
            if (result.success) {
                // Close the modal
                const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadDocumentModal'));
                uploadModal.hide();
                
                // Show success message
                this.showSuccess(`Document "${result.document.document_name}" uploaded successfully!`);
                
                // Refresh the document list
                this.loadDocuments(this.uploadingRfpId);
                
            } else {
                this.showError(result.error || 'Failed to upload document');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            this.showError('An error occurred while uploading the document');
        } finally {
            // Reset button
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = originalText;
            
            // Hide progress bar after a delay
            setTimeout(() => {
                progressBar.style.display = 'none';
            }, 2000);
        }
    }

    async saveRfp() {
        const projectName = document.getElementById('projectName').value.trim();
        const projectLink = document.getElementById('projectLink').value.trim();
        
        if (!projectName) {
            alert('Please enter a project name.');
            return;
        }
        
        // Disable save button and show loading
        const saveBtn = document.getElementById('saveRfpBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
        
        try {
            const response = await fetch('/api/rfp-create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_name: projectName,
                    link: projectLink
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addRfpModal'));
                modal.hide();
                
                // Reload the RFP list to show the new entry
                this.loadRfpList();
                
                // Select the newly created RFP
                setTimeout(() => {
                    this.selectRfp(data.rfp);
                }, 100);
                
            } else {
                alert('Error creating RFP: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving RFP:', error);
            alert('An error occurred while saving the RFP. Please try again.');
        } finally {
            // Reset button
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    editRfp(rfpId) {
        // Find the current RFP data
        const currentRfp = this.currentRfps.find(rfp => rfp.id === rfpId);
        if (!currentRfp) {
            console.error('RFP not found:', rfpId);
            return;
        }
        
        // Populate the edit form
        document.getElementById('editProjectName').value = currentRfp.project_name || '';
        document.getElementById('editOrganizationGroup').value = currentRfp.organization_group || '';
        document.getElementById('editLink').value = currentRfp.link || '';
        document.getElementById('editCountry').value = currentRfp.country || '';
        document.getElementById('editRegion').value = currentRfp.region || '';
        document.getElementById('editProjectFocus').value = currentRfp.project_focus || '';
        document.getElementById('editIndustry').value = currentRfp.industry || '';
        document.getElementById('editOpfGapSize').value = currentRfp.opf_gap_size || '';
        document.getElementById('editDueDate').value = currentRfp.due_date ? currentRfp.due_date.split('T')[0] : '';
        document.getElementById('editProjectCost').value = currentRfp.project_cost || '';
        document.getElementById('editCurrency').value = currentRfp.currency || '';
        document.getElementById('editPostingContact').value = currentRfp.posting_contact || '';
        document.getElementById('editOpfGaps').value = currentRfp.opf_gaps || '';
        document.getElementById('editDeliverables').value = currentRfp.deliverables || '';
        document.getElementById('editPotentialExperts').value = currentRfp.potential_experts || '';
        document.getElementById('editSpecificStaffingNeeds').value = currentRfp.specific_staffing_needs || '';
        
        // Store the RFP ID for the save operation
        this.editingRfpId = rfpId;
        
        // Show the modal
        const editModal = new bootstrap.Modal(document.getElementById('editRfpModal'));
        editModal.show();
    }

    async saveEditRfp() {
        try {
            const form = document.getElementById('editRfpForm');
            const formData = new FormData(form);
            
            // Convert FormData to JSON
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Make the API call
            const response = await fetch(`/api/rfp-update/${this.editingRfpId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update the current RFP in the list
                const index = this.currentRfps.findIndex(rfp => rfp.id === this.editingRfpId);
                if (index !== -1) {
                    this.currentRfps[index] = result.rfp;
                }
                
                // Refresh the display
                this.displayRfpList(this.currentRfps);
                this.displayRfpDetails(result.rfp);
                
                // Reload documents for the updated RFP
                this.loadDocuments(this.editingRfpId);
                
                // Close the modal
                const editModal = bootstrap.Modal.getInstance(document.getElementById('editRfpModal'));
                editModal.hide();
                
                // Show success message
                this.showSuccess('RFP updated successfully!');
            } else {
                this.showError(result.error || 'Failed to update RFP');
            }
        } catch (error) {
            console.error('Error updating RFP:', error);
            this.showError('An error occurred while updating the RFP');
        }
    }

    showSuccess(message) {
        // Create a temporary success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }

    async loadDocuments(rfpId) {
        try {
            const response = await fetch(`/api/documents/${rfpId}`);
            const result = await response.json();
            
            if (result.success) {
                // Store documents in the selectedRfp object
                if (this.selectedRfp && this.selectedRfp.id === rfpId) {
                    this.selectedRfp.documents = result.documents;
                }
                this.displayDocuments(result.documents);
            } else {
                console.error('Error loading documents:', result.error);
                if (this.selectedRfp && this.selectedRfp.id === rfpId) {
                    this.selectedRfp.documents = [];
                }
                this.displayDocuments([]);
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            if (this.selectedRfp && this.selectedRfp.id === rfpId) {
                this.selectedRfp.documents = [];
            }
            this.displayDocuments([]);
        }
    }

    displayDocuments(documents) {
        const documentsList = document.getElementById('documentsList');
        
        if (documents.length === 0) {
            documentsList.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-file-alt fa-2x mb-3"></i>
                    <p>No documents uploaded yet</p>
                    <small>Upload documents to see them here</small>
                </div>
            `;
            return;
        }
        
        let documentsHtml = '';
        documents.forEach(doc => {
            const uploadDate = doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown date';
            const fileExtension = doc.document_name.split('.').pop().toUpperCase();
            
            documentsHtml += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="d-flex align-items-center mb-2">
                                    <span class="badge bg-secondary me-2">${fileExtension}</span>
                                    <h6 class="mb-0">${this.escapeHtml(doc.document_name)}</h6>
                                </div>
                                <small class="text-muted">
                                    <i class="fas fa-calendar me-1"></i>Uploaded ${uploadDate}
                                </small>
                                <div class="mt-2">
                                    <small class="text-muted">
                                        <i class="fas fa-file-text me-1"></i>Text preview:
                                    </small>
                                    <p class="mt-1 mb-0" style="font-family: 'Azeret Mono', monospace; font-size: 0.85em; color: #666;">
                                        ${this.escapeHtml(doc.text_preview)}
                                    </p>
                                </div>
                            </div>
                            <div class="ms-3">
                                <button class="btn btn-outline-danger btn-sm" onclick="event.stopPropagation(); app.deleteDocument(${doc.id}, '${this.escapeHtml(doc.document_name)}')" title="Delete Document">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        documentsList.innerHTML = documentsHtml;
    }

    deleteDocument(documentId, documentName) {
        // Show confirmation dialog
        const confirmed = confirm(`Are you sure you want to delete the document "${documentName}"?\n\nThis will permanently delete:\n• The document file\n• All extracted text content\n\nThis action cannot be undone.`);
        
        if (confirmed) {
            this.performDeleteDocument(documentId);
        }
    }

    async performDeleteDocument(documentId) {
        try {
            const response = await fetch(`/api/document-delete/${documentId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                this.showSuccess(result.message);
                
                // Refresh the documents list for the current RFP
                if (result.rfp_id) {
                    this.loadDocuments(result.rfp_id);
                }
            } else {
                this.showError(result.error || 'Failed to delete document');
            }
        } catch (error) {
            console.error('Error deleting document:', error);
            this.showError('An error occurred while deleting the document');
        }
    }

    deleteRfp(rfpId, projectName) {
        // Show confirmation dialog
        const confirmed = confirm(`Are you sure you want to delete the RFP project "${projectName}"?\n\nThis will permanently delete:\n• The RFP project and all its metadata\n• All associated documents\n\nThis action cannot be undone.`);
        
        if (confirmed) {
            this.performDeleteRfp(rfpId);
        }
    }

    async performDeleteRfp(rfpId) {
        try {
            const response = await fetch(`/api/rfp-delete/${rfpId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Remove the RFP from the current list
                this.currentRfps = this.currentRfps.filter(rfp => rfp.id !== rfpId);
                
                // Refresh the display
                this.displayRfpList(this.currentRfps);
                
                // Clear the details panel if the deleted RFP was selected
                const rfpDetails = document.getElementById('rfpDetails');
                if (rfpDetails.innerHTML.includes(`app.editRfp(${rfpId})`)) {
                    rfpDetails.innerHTML = `
                        <div class="text-center text-muted">
                            <p>Choose an RFP from the list to view details and upload documents</p>
                        </div>
                    `;
                }
                
                // Show success message
                this.showSuccess('RFP project deleted successfully!');
            } else {
                this.showError(result.error || 'Failed to delete RFP');
            }
        } catch (error) {
            console.error('Error deleting RFP:', error);
            this.showError('An error occurred while deleting the RFP');
        }
    }

    generateAiAnalysis() {
        // Check if there are documents for the current RFP
        if (!this.selectedRfp) {
            alert('Please select an RFP first.');
            return;
        }
        
        if (!this.selectedRfp.documents || this.selectedRfp.documents.length === 0) {
            // Show popup for no documents
            alert('You must first upload documents to run the analysis.');
            return;
        }
        
        // Show loading state
        const aiContent = document.getElementById('aiAnalysisContent');
        aiContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Analyzing RFP against company knowledge base...</p>
                <small class="text-muted">This may take a few moments</small>
            </div>
        `;
        
        // Call AI analysis API
        fetch(`/api/ai-analyze/${this.selectedRfp.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('AI Analysis response:', data); // Debug logging
            if (data.success) {
                console.log('Analysis data:', data.analysis); // Debug logging
                
                // Check if metadata was extracted and populated
                const extractedMetadata = data.analysis.extracted_metadata || {};
                const populatedFields = Object.keys(extractedMetadata).filter(key => 
                    extractedMetadata[key] && extractedMetadata[key] !== 'null' && extractedMetadata[key] !== ''
                );
                
                if (populatedFields.length > 0) {
                    this.showSuccess(`AI Analysis completed! Automatically populated ${populatedFields.length} metadata fields: ${populatedFields.join(', ')}`);
                } else {
                    this.showSuccess('AI Analysis completed successfully!');
                }
                
                this.displayAiAnalysis(data.analysis, data.member_matching);
                
                // Refresh RFP details to show the saved analysis and populated metadata
                this.loadRfpList().then(() => {
                    const updatedRfp = this.currentRfps.find(rfp => rfp.id === this.selectedRfp.id);
                    if (updatedRfp) {
                        this.selectedRfp = updatedRfp;
                        this.displayRfpDetails(updatedRfp);
                        // Also reload documents to fix the loading state
                        this.loadDocuments(updatedRfp.id);
                    }
                });
            } else {
                this.showError(data.error || 'AI analysis failed');
                aiContent.innerHTML = `
                    <div class="text-center">
                        <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                            <i class="fas fa-robot me-2"></i>Generate AI Analysis
                        </button>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('AI Analysis error:', error);
            this.showError('An error occurred during AI analysis');
            aiContent.innerHTML = `
                <div class="text-center">
                    <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                        <i class="fas fa-robot me-2"></i>Generate AI Analysis
                    </button>
                </div>
            `;
        });
    }

    displayAiAnalysis(analysis, memberMatching = null) {
        console.log('Displaying analysis:', analysis); // Debug logging
        console.log('Member matching:', memberMatching); // Debug logging
        const aiContent = document.getElementById('aiAnalysisContent');
        
        // Check if analysis has the expected structure
        if (!analysis || typeof analysis !== 'object') {
            console.error('Invalid analysis data:', analysis);
            aiContent.innerHTML = '<div class="alert alert-danger">Invalid analysis data received</div>';
            return;
        }
        
        // Generate member matching section
        let memberMatchingHtml = '';
        if (memberMatching && memberMatching.success) {
            const keywords = memberMatching.keywords || [];
            const members = memberMatching.members || [];
            
            memberMatchingHtml = `
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header bg-dark text-white">
                                <h6 class="mb-0"><i class="fas fa-user-friends me-2"></i>Recommended Team Members</h6>
                            </div>
                            <div class="card-body">
                                ${keywords.length > 0 ? `
                                    <div class="mb-3">
                                        <strong>Expertise Keywords Identified:</strong>
                                        <div class="mt-2">
                                            ${keywords.map(keyword => `<span class="badge bg-primary me-2 mb-2">${keyword}</span>`).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${members.length > 0 ? `
                                    <div class="table-responsive">
                                        <table class="table table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Name</th>
                                                    <th>Relevance Score</th>
                                                    <th>Key Skills</th>
                                                    <th>Explanation</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${members.map(member => `
                                                    <tr>
                                                        <td>
                                                            <strong>${member.name || 'N/A'}</strong>
                                                            ${member.member_id ? `<br><small class="text-muted">ID: ${member.member_id}</small>` : ''}
                                                        </td>
                                                        <td>
                                                            <div class="d-flex align-items-center">
                                                                <div class="progress me-2" style="width: 60px; height: 8px;">
                                                                    <div class="progress-bar bg-success" style="width: ${(member.relevance_score || 5) * 10}%"></div>
                                                                </div>
                                                                <span class="badge bg-secondary">${member.relevance_score || 5}/10</span>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            ${(member.key_skills || []).map(skill => `<span class="badge bg-info me-1 mb-1">${skill}</span>`).join('')}
                                                        </td>
                                                        <td>
                                                            <small>${member.explanation || 'Member matched by keyword search'}</small>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : `
                                    <div class="alert alert-info">
                                        <i class="fas fa-info-circle me-2"></i>
                                        ${memberMatching.message || 'No relevant team members found for the identified expertise requirements.'}
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (memberMatching && !memberMatching.success) {
            memberMatchingHtml = `
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Member Matching Issue:</strong> ${memberMatching.error || 'Failed to find relevant team members'}
                        </div>
                    </div>
                </div>
            `;
        }
        
        const analysisHtml = `
            <div class="ai-analysis-results">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-chart-line me-2"></i>Fit Assessment</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.fit_assessment || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0"><i class="fas fa-users me-2"></i>Competitive Position</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.competitive_position || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0"><i class="fas fa-star me-2"></i>Key Strengths</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.key_strengths || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Gaps & Challenges</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.gaps_challenges || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-secondary text-white">
                                <h6 class="mb-0"><i class="fas fa-tools me-2"></i>Resource Requirements</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.resource_requirements || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-danger text-white">
                                <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Risk Assessment</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.risk_assessment || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div class="card mb-3">
                            <div class="card-header bg-light text-dark">
                                <h6 class="mb-0"><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${analysis.recommendations || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${memberMatchingHtml}
                
                <div class="text-center mt-3">
                    <button class="btn btn-outline-primary" onclick="app.generateAiAnalysis()">
                        <i class="fas fa-refresh me-2"></i>Re-run Analysis
                    </button>
                </div>
            </div>
        `;
        
        aiContent.innerHTML = analysisHtml;
    }

    getFitBadgeColor(fitAssessment) {
        const fit = fitAssessment.toLowerCase();
        if (fit.includes('high')) return 'success';
        if (fit.includes('medium')) return 'warning';
        if (fit.includes('low')) return 'danger';
        return 'secondary';
    }

    hasExistingAnalysis(rfp) {
        return rfp.ai_fit_assessment && rfp.ai_fit_assessment.trim() !== '';
    }

    displayExistingAnalysis(rfp) {
        const analysisDate = rfp.ai_analysis_date ? new Date(rfp.ai_analysis_date).toLocaleDateString() : 'Unknown';
        
        return `
            <div class="ai-analysis-results">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <small class="text-muted">Last analyzed: ${analysisDate}</small>
                    <div>
                        <button class="btn btn-outline-success btn-sm me-2" onclick="app.findRelevantMembers()">
                            <i class="fas fa-user-friends me-2"></i>Find Team Members
                        </button>
                        <button class="btn btn-outline-primary btn-sm" onclick="app.generateAiAnalysis()">
                            <i class="fas fa-refresh me-2"></i>Re-run Analysis
                        </button>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0"><i class="fas fa-chart-line me-2"></i>Fit Assessment</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_fit_assessment || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0"><i class="fas fa-users me-2"></i>Competitive Position</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_competitive_position || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0"><i class="fas fa-star me-2"></i>Key Strengths</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_key_strengths || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Gaps & Challenges</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_gaps_challenges || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-secondary text-white">
                                <h6 class="mb-0"><i class="fas fa-tools me-2"></i>Resource Requirements</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_resource_requirements || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-danger text-white">
                                <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Risk Assessment</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_risk_assessment || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div class="card mb-3">
                            <div class="card-header bg-light text-dark">
                                <h6 class="mb-0"><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
                            </div>
                            <div class="card-body">
                                <p class="mb-0">${rfp.ai_recommendations || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    findRelevantMembers() {
        if (!this.selectedRfp) {
            this.showError('Please select an RFP first.');
            return;
        }
        
        // Show loading state
        const aiContent = document.getElementById('aiAnalysisContent');
        const currentContent = aiContent.innerHTML;
        
        aiContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-success" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Finding relevant team members...</p>
                <small class="text-muted">This may take a few moments</small>
            </div>
        `;
        
        // Call member matching API
        fetch(`/api/rfp/${this.selectedRfp.id}/find-members`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Member matching response:', data);
            
            if (data.success) {
                this.showSuccess('Team member matching completed!');
                
                // Re-display the existing analysis with member matching results
                const analysis = {
                    fit_assessment: this.selectedRfp.ai_fit_assessment || '',
                    competitive_position: this.selectedRfp.ai_competitive_position || '',
                    key_strengths: this.selectedRfp.ai_key_strengths || '',
                    gaps_challenges: this.selectedRfp.ai_gaps_challenges || '',
                    resource_requirements: this.selectedRfp.ai_resource_requirements || '',
                    risk_assessment: this.selectedRfp.ai_risk_assessment || '',
                    recommendations: this.selectedRfp.ai_recommendations || ''
                };
                
                this.displayAiAnalysis(analysis, data);
            } else {
                this.showError(data.error || 'Failed to find relevant team members');
                aiContent.innerHTML = currentContent;
            }
        })
        .catch(error => {
            console.error('Member matching error:', error);
            this.showError('An error occurred while finding team members');
            aiContent.innerHTML = currentContent;
        });
    }

    async initKnowledgeBase() {
        try {
            // Show loading state
            const aiContent = document.getElementById('aiAnalysisContent');
            aiContent.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3">Initializing knowledge base...</p>
                    <small class="text-muted">This may take a few minutes</small>
                </div>
            `;
            
            // Call the initialization endpoint
            const response = await fetch('/api/init-knowledge-base', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})  // Send empty JSON object instead of no body
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.already_initialized) {
                    // Knowledge base was already initialized
                    this.showSuccess(data.message);
                } else {
                    // Knowledge base was newly initialized
                    this.showSuccess(data.message);
                }
                
                // Reset to the normal AI analysis interface
                aiContent.innerHTML = `
                    <div class="text-center">
                        <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                            <i class="fas fa-robot me-2"></i>Generate AI Analysis
                        </button>
                        <div class="mt-2">
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.initKnowledgeBase()">
                                <i class="fas fa-database me-2"></i>Initialize Knowledge Base
                            </button>
                        </div>
                    </div>
                `;
            } else {
                this.showError(data.error || 'Failed to initialize knowledge base');
                // Reset to normal interface
                aiContent.innerHTML = `
                    <div class="text-center">
                        <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                            <i class="fas fa-robot me-2"></i>Generate AI Analysis
                        </button>
                        <div class="mt-2">
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.initKnowledgeBase()">
                                <i class="fas fa-database me-2"></i>Initialize Knowledge Base
                            </button>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Knowledge base initialization error:', error);
            this.showError('An error occurred during knowledge base initialization');
            // Reset to normal interface
            aiContent.innerHTML = `
                <div class="text-center">
                    <button class="btn btn-primary" onclick="app.generateAiAnalysis()">
                        <i class="fas fa-robot me-2"></i>Generate AI Analysis
                    </button>
                    <div class="mt-2">
                        <button class="btn btn-outline-secondary btn-sm" onclick="app.initKnowledgeBase()">
                            <i class="fas fa-database me-2"></i>Initialize Knowledge Base
                        </button>
                    </div>
                </div>
            `;
        }
    }

    async checkKnowledgeBaseStatus() {
        try {
            const response = await fetch('/api/knowledge-base-status');
            const data = await response.json();
            
            if (data.success) {
                if (data.status === 'initialized') {
                    this.showSuccess(`Knowledge base is ready with ${data.document_count} document chunks`);
                } else {
                    this.showError('Knowledge base is not initialized');
                }
            } else {
                this.showError(data.error || 'Failed to check knowledge base status');
            }
        } catch (error) {
            console.error('Error checking knowledge base status:', error);
            this.showError('An error occurred while checking knowledge base status');
        }
    }



    async scrapeAustralianTenders() {
        const scrapeBtn = document.getElementById('scrapeAusTendersBtn') || document.getElementById('scrapeAusTendersBtn2');
        const originalText = scrapeBtn.innerHTML;
        
        try {
            // Show loading state
            scrapeBtn.disabled = true;
            scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scraping...';
            
            const response = await fetch('/api/tenders/scrape-aus', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success !== undefined) {
                // Show success message
                this.showNotification(result.message || 'Australian tenders scraped successfully!', 'success');
                
                // Refresh Australian tenders list and stats
                await this.loadTendersBySource('Australian Government Tenders');
                await this.loadTendersStats();
            } else {
                throw new Error(result.error || 'Scraping failed');
            }
            
        } catch (error) {
            console.error('Error scraping Australian tenders:', error);
            this.showNotification(`Australian scraping failed: ${error.message}`, 'error');
        } finally {
            // Reset button state
            scrapeBtn.disabled = false;
            scrapeBtn.innerHTML = originalText;
        }
    }

    async scrapeGizTenders() {
        const scrapeBtn = document.getElementById('scrapeGizTendersBtn') || document.getElementById('scrapeGizTendersBtn2');
        const originalText = scrapeBtn.innerHTML;
        
        try {
            // Show loading state
            scrapeBtn.disabled = true;
            scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scraping...';
            
            const response = await fetch('/api/tenders/scrape-giz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success !== undefined) {
                // Show success message
                this.showNotification(result.message || 'GIZ tenders scraped successfully!', 'success');
                
                // Refresh GIZ tenders list and stats
                await this.loadTendersBySource('GIZ (German Development Agency)');
                await this.loadTendersStats();
            } else {
                throw new Error(result.error || 'Scraping failed');
            }
            
        } catch (error) {
            console.error('Error scraping GIZ tenders:', error);
            this.showNotification(`GIZ scraping failed: ${error.message}`, 'error');
        } finally {
            // Reset button state
            scrapeBtn.disabled = false;
            scrapeBtn.innerHTML = originalText;
        }
    }

    async scrapeUndpTenders() {
        const scrapeBtn = document.getElementById('scrapeUndpTendersBtn2');
        const originalText = scrapeBtn.innerHTML;
        
        try {
            // Show loading state
            scrapeBtn.disabled = true;
            scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scraping...';
            
            const response = await fetch('/api/tenders/scrape-undp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success !== undefined) {
                // Show success message
                this.showNotification(result.message || 'UNDP tenders scraped successfully!', 'success');
                
                // Refresh UNDP tenders list and stats
                await this.loadTendersBySource('UNDP (United Nations Development Programme)');
                await this.loadTendersStats();
            } else {
                throw new Error(result.error || 'Scraping failed');
            }
            
        } catch (error) {
            console.error('Error scraping UNDP tenders:', error);
            this.showNotification(`UNDP scraping failed: ${error.message}`, 'error');
        } finally {
            // Reset button state
            scrapeBtn.disabled = false;
            scrapeBtn.innerHTML = originalText;
        }
    }
    
    async loadTendersList(filter = 'all') {
        try {
            const tendersList = document.getElementById('tendersList');
            const noTendersMessage = document.getElementById('noTendersMessage');
            const tendersLoading = document.getElementById('tendersLoading');
            
            // Show loading
            tendersList.style.display = 'none';
            noTendersMessage.style.display = 'none';
            tendersLoading.style.display = 'block';
            
            // Build query parameters
            const params = new URLSearchParams();
            if (filter === 'unprocessed') {
                params.append('processed', 'false');
            } else if (filter === 'processed') {
                params.append('processed', 'true');
            }
            
            const response = await fetch(`/api/tenders/list?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                if (result.tenders.length === 0) {
                    noTendersMessage.style.display = 'block';
                } else {
                    this.renderTendersList(result.tenders);
                    tendersList.style.display = 'block';
                }
            } else {
                throw new Error(result.error || 'Failed to load tenders');
            }
            
        } catch (error) {
            console.error('Error loading tenders:', error);
            this.showNotification(`Failed to load tenders: ${error.message}`, 'error');
        } finally {
            document.getElementById('tendersLoading').style.display = 'none';
        }
    }
    
    renderTendersList(tenders) {
        const tendersList = document.getElementById('tendersList');
        tendersList.innerHTML = '';
        
        tenders.forEach(tender => {
            const tenderItem = document.createElement('div');
            tenderItem.className = 'list-group-item list-group-item-action';
            tenderItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${this.escapeHtml(tender.title)}</h6>
                        <p class="mb-1 text-muted small">${this.escapeHtml(tender.description || '')}</p>
                        <div class="d-flex align-items-center gap-3">
                            <small class="text-muted">
                                <i class="fas fa-building me-1"></i>${this.escapeHtml(tender.organization)}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-calendar me-1"></i>${tender.closing_date || 'No deadline'}
                            </small>
                            <small class="fas fa-globe me-1"></i>${this.escapeHtml(tender.source)}
                            </small>
                            <span class="badge ${tender.processed ? 'bg-success' : 'bg-warning'}">
                                ${tender.processed ? 'Processed' : 'Unprocessed'}
                            </span>
                        </div>
                    </div>
                    <div class="ms-3">
                        <div class="btn-group-vertical btn-group-sm">
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.toggleTenderProcessed(${tender.id}, ${!tender.processed})">
                                <i class="fas fa-${tender.processed ? 'undo' : 'check'}"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            tendersList.appendChild(tenderItem);
        });
    }
    
    async toggleTenderProcessed(tenderId, processed) {
        try {
            const response = await fetch('/api/tenders/mark-processed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tender_id: tenderId,
                    processed: processed
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                
                // Determine which tab is currently active and refresh accordingly
                const activeTab = document.querySelector('.nav-link.active');
                if (activeTab) {
                    const tabId = activeTab.getAttribute('id');
                    
                                    if (tabId === 'australian-tenders-tab') {
                    // Refresh Australian tenders list
                    await this.loadTendersBySource('Australian Government Tenders');
                } else if (tabId === 'giz-tenders-tab') {
                    // Refresh GIZ tenders list
                    await this.loadTendersBySource('GIZ (German Development Agency)');
                } else if (tabId === 'undp-tenders-tab') {
                    // Refresh UNDP tenders list
                    await this.loadTendersBySource('UNDP (United Nations Development Programme)');
                }
                }
                
                // Refresh stats
                await this.loadTendersStats();
            } else {
                throw new Error(result.error || 'Failed to update tender');
            }
            
        } catch (error) {
            console.error('Error updating tender:', error);
            this.showNotification(`Failed to update tender: ${error.message}`, 'error');
        }
    }
    
    async loadTendersStats() {
        try {
            const response = await fetch('/api/tenders/stats');
            const result = await response.json();
            
            if (result.success) {
                // Only update stats if the elements exist (they might not in individual tabs)
                const totalCountElement = document.getElementById('totalTendersCount');
                const unprocessedCountElement = document.getElementById('unprocessedCount');
                const lastScrapedElement = document.getElementById('lastScrapedDate');
                
                if (totalCountElement) {
                    totalCountElement.textContent = result.total_tenders;
                }
                if (unprocessedCountElement) {
                    unprocessedCountElement.textContent = result.total_unprocessed;
                }
                
                // Show last scraped date if element exists
                if (lastScrapedElement && result.recent_activity && result.recent_activity.length > 0) {
                    const lastDate = new Date(result.recent_activity[0].date);
                    lastScrapedElement.textContent = lastDate.toLocaleDateString();
                } else if (lastScrapedElement) {
                    lastScrapedElement.textContent = 'Never';
                }
            }
        } catch (error) {
            console.error('Error loading tender stats:', error);
        }
    }
    
    filterTenders(filter) {
        this.loadTendersList(filter);
    }

    filterTendersBySource(source, filter = 'all') {
        this.loadTendersBySource(source, filter);
    }

    async loadTendersBySource(source, filter = 'all') {
        try {
            let listElement, noMessageElement, loadingElement;
            
            // Determine which elements to use based on source
            if (source === 'Australian Government Tenders') {
                listElement = document.getElementById('australianTendersList');
                noMessageElement = document.getElementById('noAustralianTendersMessage');
                loadingElement = document.getElementById('australianTendersLoading');
            } else if (source === 'GIZ (German Development Agency)') {
                listElement = document.getElementById('gizTendersList');
                noMessageElement = document.getElementById('noGizTendersMessage');
                loadingElement = document.getElementById('gizTendersLoading');
            } else if (source === 'UNDP (United Nations Development Programme)') {
                listElement = document.getElementById('undpTendersList');
                noMessageElement = document.getElementById('noUndpTendersMessage');
                loadingElement = document.getElementById('undpTendersLoading');
            } else {
                console.error('Unknown source:', source);
                return;
            }
            
            // Show loading
            listElement.style.display = 'none';
            noMessageElement.style.display = 'none';
            loadingElement.style.display = 'block';
            
            // Build query parameters
            const params = new URLSearchParams();
            params.append('source', source);
            if (filter === 'unprocessed') {
                params.append('processed', 'false');
            } else if (filter === 'processed') {
                params.append('processed', 'true');
            }
            
            const response = await fetch(`/api/tenders/list?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                if (result.tenders.length === 0) {
                    noMessageElement.style.display = 'block';
                } else {
                    this.renderTendersListBySource(result.tenders, source);
                    listElement.style.display = 'block';
                }
            } else {
                throw new Error(result.error || 'Failed to load tenders');
            }
            
        } catch (error) {
            console.error('Error loading tenders by source:', error);
            this.showNotification(`Failed to load tenders: ${error.message}`, 'error');
        } finally {
            // Hide loading for the appropriate source
            if (source === 'Australian Government Tenders') {
                document.getElementById('australianTendersLoading').style.display = 'none';
            } else if (source === 'GIZ (German Development Agency)') {
                document.getElementById('gizTendersLoading').style.display = 'none';
            } else if (source === 'UNDP (United Nations Development Programme)') {
                document.getElementById('undpTendersLoading').style.display = 'none';
            }
        }
    }

    renderTendersListBySource(tenders, source) {
        let listElement;
        
        if (source === 'Australian Government Tenders') {
            listElement = document.getElementById('australianTendersList');
        } else if (source === 'GIZ (German Development Agency)') {
            listElement = document.getElementById('gizTendersList');
        } else if (source === 'UNDP (United Nations Development Programme)') {
            listElement = document.getElementById('undpTendersList');
        } else {
            return;
        }
        
        listElement.innerHTML = '';
        
        tenders.forEach(tender => {
            const tenderItem = document.createElement('div');
            tenderItem.className = 'list-group-item list-group-item-action';
            tenderItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${this.escapeHtml(tender.title)}</h6>
                        <p class="mb-1 text-muted small">${this.escapeHtml(tender.description || '')}</p>
                        <div class="d-flex align-items-center gap-3">
                            <small class="text-muted">
                                <i class="fas fa-building me-1"></i>${this.escapeHtml(tender.organization)}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-calendar me-1"></i>${tender.closing_date || 'No deadline'}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-globe me-1"></i>${this.escapeHtml(tender.source)}
                            </small>
                            <span class="badge ${tender.processed ? 'bg-success' : 'bg-warning'}">
                                ${tender.processed ? 'Processed' : 'Unprocessed'}
                            </span>
                        </div>
                    </div>
                    <div class="ms-3">
                        <div class="btn-group-vertical btn-group-sm">
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.toggleTenderProcessed(${tender.id}, ${!tender.processed})">
                                <i class="fas fa-${tender.processed ? 'undo' : 'check'}"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            listElement.appendChild(tenderItem);
        });
    }


    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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