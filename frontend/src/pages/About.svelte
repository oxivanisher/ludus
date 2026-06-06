<script>
  import { _ } from 'svelte-i18n';

  let { onBack } = $props();
</script>

<div class="flex flex-col gap-8 max-w-prose">
  <div>
    <button
      class="inline-flex items-center gap-1 text-sm px-3 py-1.5 mb-4 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
      onclick={onBack}
    >
      {$_('history.back')}
    </button>
    <h1 class="text-2xl font-bold">{$_('about.title')}</h1>
  </div>

  <!-- What is Ludus -->
  <section class="flex flex-col gap-2">
    <h2 class="text-lg font-semibold">{$_('about.what_title')}</h2>
    <p class="text-gray-700 dark:text-gray-300 leading-relaxed">{$_('about.what_body')}</p>
  </section>

  <!-- Privacy -->
  <section class="flex flex-col gap-2">
    <h2 class="text-lg font-semibold">{$_('about.privacy_title')}</h2>
    <p class="text-gray-700 dark:text-gray-300 leading-relaxed">{$_('about.privacy_body')}</p>
    <ul class="flex flex-col gap-1.5 mt-1">
      {#each $_('about.privacy_points') as point}
        <li class="flex gap-2 text-gray-700 dark:text-gray-300 leading-relaxed">
          <span class="text-green-600 dark:text-green-400 mt-0.5 shrink-0">✓</span>
          <span>{point}</span>
        </li>
      {/each}
    </ul>
  </section>

  <!-- Token -->
  <section class="flex flex-col gap-2 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900">
    <h2 class="text-lg font-semibold">{$_('about.token_title')}</h2>
    <p class="text-gray-700 dark:text-gray-300 leading-relaxed">{$_('about.token_body')}</p>
    <ul class="flex flex-col gap-1.5 mt-1">
      {#each $_('about.token_points') as point}
        <li class="flex gap-2 text-gray-700 dark:text-gray-300 leading-relaxed">
          <span class="text-indigo-500 dark:text-indigo-400 mt-0.5 shrink-0">•</span>
          <span>{point}</span>
        </li>
      {/each}
    </ul>
  </section>

  <!-- Self-hosting -->
  <section class="flex flex-col gap-2">
    <h2 class="text-lg font-semibold">{$_('about.selfhost_title')}</h2>
    <p class="text-gray-700 dark:text-gray-300 leading-relaxed">{$_('about.selfhost_body')}</p>
    <a
      href="https://github.com/oxivanisher/ludus"
      target="_blank"
      rel="noopener noreferrer"
      class="text-indigo-600 dark:text-indigo-400 hover:underline font-mono text-sm w-fit"
    >{$_('about.selfhost_github')}</a>
  </section>
</div>
