// TalkToText Pro — Client-Side Application Scripts

function initTheme() {
  const savedTheme = localStorage.getItem('ttt_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'dark');
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    document.documentElement.setAttribute('data-theme', 'light');
  }
  localStorage.setItem('ttt_theme', theme);
  updateThemeIcons(theme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
  showToast(`Switched to ${newTheme === 'dark' ? 'Dark' : 'Light'} Mode`, 'info');
}

function updateThemeIcons(theme) {
  const themeIcons = document.querySelectorAll('.theme-toggle-icon');
  themeIcons.forEach(icon => {
    if (theme === 'dark') {
      icon.innerHTML = `<svg class="w-4 h-4 text-amber-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`;
    } else {
      icon.innerHTML = `<svg class="w-4 h-4 text-slate-700" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
    }
  });
}

initTheme();

document.addEventListener('DOMContentLoaded', () => {
  initTheme();

  if (window.lucide) {
    lucide.createIcons();
  }

  // Tab Navigation
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.tagName === 'A' && btn.getAttribute('href')) return;

      const targetId = btn.getAttribute('data-tab');
      if (!targetId) return;

      tabButtons.forEach(b => {
        b.classList.remove('active', 'border-brand-500', 'text-brand-400', 'bg-brand-500/10');
        b.classList.add('border-transparent', 'text-slate-400', 'hover:text-slate-200');
      });
      tabPanes.forEach(p => p.classList.add('hidden'));

      btn.classList.add('active', 'border-brand-500', 'text-brand-400', 'bg-brand-500/10');
      btn.classList.remove('border-transparent', 'text-slate-400');

      const target = document.getElementById(targetId);
      if (target) target.classList.remove('hidden');
    });
  });

  // Audio Recording
  const recordBtn = document.getElementById('recordBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  const recordTimer = document.getElementById('recordTimer');
  const recordingPulseIndicator = document.getElementById('recordingPulseIndicator');
  const audioInput = document.getElementById('audioInput');
  const recordedAudioPreview = document.getElementById('recordedAudioPreview');

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let isPaused = false;
  let recordedSeconds = 0;
  let timerInterval = null;

  if (recordBtn) {
    recordBtn.addEventListener('click', async () => {
      if (!isRecording) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
          };

          mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/wav' });
            const file = new File([blob], `Recording_${Date.now()}.wav`, { type: 'audio/wav' });

            const dt = new DataTransfer();
            dt.items.add(file);
            if (audioInput) {
              audioInput.files = dt.files;
              displaySelectedFile(file);
            }

            if (recordedAudioPreview) {
              recordedAudioPreview.src = URL.createObjectURL(blob);
              recordedAudioPreview.classList.remove('hidden');
            }
          };

          mediaRecorder.start();
          isRecording = true;
          isPaused = false;

          recordBtn.innerHTML = `<svg class="w-4 h-4 text-rose-400 animate-spin mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Stop Recording`;
          recordBtn.classList.remove('bg-rose-600', 'hover:bg-rose-500');
          recordBtn.classList.add('bg-rose-700', 'hover:bg-rose-600', 'animate-pulse');

          if (pauseBtn) pauseBtn.classList.remove('hidden');
          if (recordingPulseIndicator) recordingPulseIndicator.classList.remove('hidden');

          recordedSeconds = 0;
          updateTimerText();
          timerInterval = setInterval(() => {
            if (!isPaused) {
              recordedSeconds++;
              updateTimerText();
            }
          }, 1000);

          showToast('Live microphone recording active...', 'info');
        } catch (err) {
          showToast('Microphone access denied: ' + err.message, 'error');
        }
      } else {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
          mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
        clearInterval(timerInterval);
        isRecording = false;
        recordBtn.innerHTML = `<span>🎙️</span> Record Voice Memo`;
        recordBtn.classList.remove('bg-rose-700', 'hover:bg-rose-600', 'animate-pulse');
        recordBtn.classList.add('bg-rose-600', 'hover:bg-rose-500');

        if (pauseBtn) pauseBtn.classList.add('hidden');
        if (recordingPulseIndicator) recordingPulseIndicator.classList.add('hidden');
        showToast('Recording attached successfully!', 'success');
      }
    });

    if (pauseBtn) {
      pauseBtn.addEventListener('click', () => {
        if (!isRecording) return;
        if (!isPaused) {
          mediaRecorder.pause();
          isPaused = true;
          pauseBtn.innerHTML = '<span>▶️</span> Resume';
          showToast('Recording paused', 'info');
        } else {
          mediaRecorder.resume();
          isPaused = false;
          pauseBtn.innerHTML = '<span>⏸</span> Pause';
          showToast('Recording resumed', 'info');
        }
      });
    }
  }

  function updateTimerText() {
    if (recordTimer) {
      const mins = String(Math.floor(recordedSeconds / 60)).padStart(2, '0');
      const secs = String(recordedSeconds % 60).padStart(2, '0');
      recordTimer.textContent = `${mins}:${secs}`;
    }
  }

  // Drag and Drop Uploads
  const dropzone = document.getElementById('dropzone');
  const selectedFileDisplay = document.getElementById('selectedFileDisplay');
  const fileNameText = document.getElementById('fileNameText');

  if (dropzone && audioInput) {
    dropzone.addEventListener('click', () => audioInput.click());

    ['dragenter', 'dragover'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        dropzone.classList.add('border-brand-500', 'bg-brand-500/10');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-brand-500', 'bg-brand-500/10');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files.length > 0) {
        audioInput.files = e.dataTransfer.files;
        displaySelectedFile(e.dataTransfer.files[0]);
      }
    });

    audioInput.addEventListener('change', () => {
      if (audioInput.files.length > 0) {
        displaySelectedFile(audioInput.files[0]);
      }
    });
  }

  function displaySelectedFile(file) {
    if (selectedFileDisplay && fileNameText) {
      fileNameText.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
      selectedFileDisplay.classList.remove('hidden');
    }
  }

  // Processing Progress Modal
  const uploadForm = document.getElementById('uploadForm');
  const aiProcessingModal = document.getElementById('aiProcessingModal');
  const progressFill = document.getElementById('progressFill');
  const progressPercent = document.getElementById('progressPercent');

  if (uploadForm && aiProcessingModal) {
    uploadForm.addEventListener('submit', () => {
      aiProcessingModal.classList.remove('hidden');
      aiProcessingModal.classList.add('flex');
      let progress = 15;
      const interval = setInterval(() => {
        if (progress < 90) {
          progress += Math.floor(Math.random() * 8) + 4;
          if (progressFill) progressFill.style.width = `${progress}%`;
          if (progressPercent) progressPercent.textContent = `Analyzing & Transcribing (${progress}%)...`;
        }
      }, 450);
    });
  }

  // Meeting AI Chat Form
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');

  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = chatInput.value.trim();
      if (!question) return;

      const meetingId = chatForm.getAttribute('data-meeting-id');
      appendChatBubble(question, 'user');
      chatInput.value = '';

      const typing = appendChatBubble('AI Copilot is analyzing meeting transcript...', 'ai', true);

      try {
        const response = await fetch(`/meeting/${meetingId}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: question })
        });
        const data = await response.json();
        typing.remove();
        if (data.reply) {
          appendChatBubble(data.reply, 'ai');
        } else {
          appendChatBubble('Could not retrieve answer.', 'ai');
        }
      } catch (err) {
        typing.remove();
        appendChatBubble('Error contacting assistant service.', 'ai');
      }
    });
  }

  function appendChatBubble(text, sender, isTyping = false) {
    const bubble = document.createElement('div');
    bubble.className = `p-3 rounded-2xl text-xs sm:text-sm max-w-[85%] ${
      sender === 'user'
        ? 'ml-auto bg-brand-600 text-white rounded-tr-none'
        : 'mr-auto bg-slate-800 border border-slate-700 text-slate-200 rounded-tl-none'
    } ${isTyping ? 'animate-pulse text-slate-400 italic' : ''}`;

    bubble.innerHTML = `<div class="font-semibold text-[11px] mb-1 opacity-75">${
      sender === 'user' ? 'You' : 'AI Copilot'
    }</div><div>${text}</div>`;

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  // Keyboard Shortcuts (Command Palette)
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const palette = document.getElementById('commandPaletteModal');
      if (palette) {
        if (palette.classList.contains('hidden')) {
          palette.classList.remove('hidden');
          palette.classList.add('flex');
          const inp = document.getElementById('paletteSearchInput');
          if (inp) inp.focus();
        } else {
          palette.classList.add('hidden');
          palette.classList.remove('flex');
        }
      }
    }
    if (e.key === 'Escape') {
      const palette = document.getElementById('commandPaletteModal');
      if (palette) {
        palette.classList.add('hidden');
        palette.classList.remove('flex');
      }
      const taskModal = document.getElementById('addTaskModal');
      if (taskModal) {
        taskModal.classList.add('hidden');
        taskModal.classList.remove('flex');
      }
    }
  });
});

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  const colorClasses = type === 'error' 
    ? 'bg-rose-950/90 border-rose-800 text-rose-200' 
    : type === 'info'
    ? 'bg-sky-950/90 border-sky-800 text-sky-200'
    : 'bg-emerald-950/90 border-emerald-800 text-emerald-200';

  toast.className = `pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-md text-xs sm:text-sm font-medium transition-all duration-300 transform translate-y-2 opacity-0 ${colorClasses}`;
  toast.innerHTML = `<span>${type === 'error' ? '⚠️' : type === 'info' ? 'ℹ️' : '✓'}</span> <span>${message}</span>`;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '🔒';
  } else {
    input.type = 'password';
    btn.innerHTML = '👁️';
  }
}

async function toggleActionItem(checkbox, meetingId, itemId) {
  try {
    const res = await fetch(`/meeting/${meetingId}/action-item/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId })
    });
    const data = await res.json();
    const row = checkbox.closest('tr') || checkbox.closest('.action-item-row');
    const textSpan = row ? row.querySelector('.task-text') : null;

    if (data.status === 'Completed') {
      if (textSpan) textSpan.classList.add('line-through', 'text-slate-500');
      showToast('Task marked as completed', 'success');
    } else {
      if (textSpan) textSpan.classList.remove('line-through', 'text-slate-500');
      showToast('Task marked as pending', 'info');
    }
  } catch (e) {
    showToast('Failed to update task status', 'error');
  }
}

function copyShareLink(url) {
  navigator.clipboard.writeText(url).then(() => {
    showToast('Shareable link copied to clipboard!', 'success');
  });
}
