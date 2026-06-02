<script>
  import { onMount } from "svelte";
  import { _ } from 'svelte-i18n';
  import QRCode from "qrcode";
  import { exportToken, buildImportUrl, importToken } from "../lib/token.js";

  let { onClose } = $props();

  const token = exportToken();
  const importUrl = buildImportUrl(token);

  let qrDataUrl = $state("");
  let copied = $state(false);
  let importValue = $state("");
  let showImportWarning = $state(false);

  onMount(async () => {
    qrDataUrl = await QRCode.toDataURL(importUrl, { width: 220, margin: 1 });
  });

  async function copyToken() {
    await navigator.clipboard.writeText(token);
    copied = true;
    setTimeout(() => { copied = false; }, 2000);
  }

  function confirmImport() {
    if (!importValue.trim()) return;
    showImportWarning = true;
  }

  function doImport() {
    importToken(importValue.trim());
  }
</script>

<!-- Backdrop -->
<div
  class="fixed inset-0 z-40 bg-black/40 flex items-center justify-center p-4"
  role="dialog"
  aria-modal="true"
>
  <div class="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 space-y-5
              dark:bg-gray-800 dark:shadow-black/60">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">{$_('token_manager.title')}</h2>
      <button class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-xl leading-none" onclick={onClose}>
        ×
      </button>
    </div>

    <p class="text-sm text-gray-500 dark:text-gray-400">
      {$_('token_manager.description')}
    </p>

    <!-- Token string -->
    <div>
      <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{$_('token_manager.your_token')}</p>
      <div class="flex gap-2">
        <code class="flex-1 bg-gray-100 rounded px-2 py-1 text-xs break-all dark:bg-gray-700 dark:text-gray-200">
          {token}
        </code>
        <button
          class="shrink-0 px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
          onclick={copyToken}
        >
          {copied ? $_('token_manager.copied') : $_('token_manager.copy')}
        </button>
      </div>
    </div>

    <!-- QR code -->
    <div class="text-center">
      <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">
        {$_('token_manager.qr_hint')}
      </p>
      {#if qrDataUrl}
        <img src={qrDataUrl} alt="Import QR code" class="mx-auto rounded border dark:border-gray-600" />
      {:else}
        <div class="w-[220px] h-[220px] mx-auto bg-gray-100 rounded animate-pulse dark:bg-gray-700"></div>
      {/if}
    </div>

    <hr class="dark:border-gray-700" />

    <!-- Import section -->
    <div>
      <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{$_('token_manager.import_label')}</p>
      <div class="flex gap-2">
        <input
          class="flex-1 border rounded px-2 py-1 text-sm font-mono
                 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
          placeholder={$_('token_manager.import_placeholder')}
          bind:value={importValue}
        />
        <button
          class="px-3 py-1 bg-yellow-600 text-white rounded text-sm disabled:opacity-50 hover:bg-yellow-700"
          disabled={!importValue.trim()}
          onclick={confirmImport}
        >
          {$_('token_manager.import_btn')}
        </button>
      </div>
    </div>

    <!-- Confirmation step -->
    {#if showImportWarning}
      <div class="p-3 bg-yellow-50 border border-yellow-300 rounded text-sm space-y-2
                  dark:bg-yellow-900/30 dark:border-yellow-700">
        <p class="text-yellow-900 dark:text-yellow-200">
          {$_('token_manager.warning')}
        </p>
        <div class="flex gap-2">
          <button class="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700" onclick={doImport}>
            {$_('token_manager.confirm_import')}
          </button>
          <button
            class="px-3 py-1 border rounded text-sm dark:border-gray-600 dark:text-gray-300"
            onclick={() => { showImportWarning = false; }}
          >
            {$_('token_manager.cancel')}
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
