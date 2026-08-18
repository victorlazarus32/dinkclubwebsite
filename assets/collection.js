/* Dink Club — the 2026 collection.
   Single source of truth, shared by the shop grid and the product page.
   Add or reorder a design here and both pages follow. */

const LINES = {
  heritage:    {label:'Heritage',    blurb:'Illustrated, built to last'},
  crest:       {label:'Crest',       blurb:'Back-print heraldry, olive body'},
  signature:   {label:'Signature',   blurb:'The everyday club tee'},
  performance: {label:'Performance', blurb:'Match-day technical fit'},
  mascot:      {label:'Mascot',      blurb:'Loud on purpose'},
};

/* Applied to every design unless the entry overrides it. Provisional until the
   Printful garments are chosen — the two No Fly Zone pieces are cut-specific. */
const SIZES = ['XS','S','M','L','XL','2XL','3XL'];
const FITS  = ['Unisex',"Women's"];

const COLLECTION = [
  {slug:'art-of-the-dink',  line:'heritage',    name:'The Art of the Dink',
   desc:"Hokusai's Great Wave, reimagined with a ball arcing over the net at sunrise.",
   tag:'Navy · Unisex Tee',
   alt:'The Art of the Dink navy tee — Great Wave illustration with a pickleball cresting over a net'},


  {slug:'no-fly-zone-mens', line:'heritage',    name:'No Fly Zone — Men’s',
   desc:'Protect the line. Overhead put-away, crosshairs, and a shield that means business.',
   tag:'Heather Grey · Men’s Cut', fits:["Men's"],
   alt:'No Fly Zone heather grey tee, men’s cut — player overhead smash with target crosshair'},

  {slug:'no-fly-zone-womens',line:'heritage',   name:'No Fly Zone — Women’s',
   desc:'Same creed, women’s cut. Protect the line.',
   tag:'Black · Women’s Cut', fits:["Women's"],
   alt:'No Fly Zone black tee, women’s cut — player overhead smash with target crosshair'},

  {slug:'dink-of-thrones',  line:'heritage',    name:'Dink of Thrones',
   desc:'A throne forged from paddles. The court is my kingdom.',
   tag:'Black · Unisex Tee',
   alt:'Dink of Thrones black tee — throne built from pickleball paddles with a crowned DC crest'},

  {slug:'octopus',          line:'crest',       name:'The Kraken',
   desc:'Crossed paddles, five stars, one very serious octopus. Full back print.',
   tag:'Olive · Back Print',
   alt:'The Kraken olive tee — line-art octopus crest with crossed paddles and a Dink Club banner'},

  {slug:'crest-lion',       line:'crest',       name:'The Lion',
   desc:'Crowned and framed in laurel. The one that says you run the place.',
   tag:'Olive · Back Print',
   alt:'The Lion olive tee — crowned lion crest above crossed paddles in a laurel wreath'},

  {slug:'crest-stag',       line:'crest',       name:'The Stag',
   desc:'Antlers made of paddles, ball rising behind. Quietest of the four, and the sharpest.',
   tag:'Olive · Back Print',
   alt:'The Stag olive tee — stag crest with paddle antlers and a rising pickleball'},

  {slug:'crest-eagle',      line:'crest',       name:'The Eagle',
   desc:'Wings open over the monogram. Full-width back print, no notes.',
   tag:'Olive · Back Print',
   alt:'The Eagle olive tee — eagle crest with spread wings over the DC monogram'},

  {slug:'speed-up',         line:'signature',   name:'Speed Up',
   desc:'The wordmark, mid-flight. Clean front hit for people who let the game talk.',
   tag:'Navy · Unisex Tee',
   alt:'Dink Club Speed Up navy tee — logo wordmark with a motion streak effect'},

  {slug:'dink-around-find-out',line:'signature',name:'Dink Around &amp; Find Out',
   desc:'Crowned skull, cracked court, zero apologies. The one your league opponents will hate.',
   tag:'Black · Unisex Tee',
   alt:'Dink Around and Find Out black tee — crowned skull inside a pickleball'},

  {slug:'tempo',            line:'signature',   name:'Touch · Tempo · Target',
   desc:'Minimal chevron mark. The quietest shirt in the collection, and probably the most worn.',
   tag:'White · Unisex Tee',
   alt:'Dink Club Performance white tee — chevron mark with Touch Tempo Target tagline'},

  {slug:'court-culture',    line:'signature',   name:'Court Culture',
   desc:'Play, connect, compete. Stacked type over a court-line texture.',
   tag:'Black · Unisex Tee',
   alt:'Court Culture black tee — Dink Club logo above layered Court Culture typography'},

  {slug:'performance-01',   line:'performance', name:'Performance 01 — Slipstream',
   desc:'Contour lines pulling through the monogram. Moisture-wicking match-day fit.',
   tag:'Navy · Performance Poly',
   alt:'Dink Club Performance 01 navy tee — flowing contour-line graphic around the DC monogram'},

  {slug:'performance-02',   line:'performance', name:'Performance 02 — Prism',
   desc:'Overlapping colour planes and a hard yellow ball at dead centre.',
   tag:'Bone · Performance Poly',
   alt:'Dink Club Performance 02 bone tee — prismatic geometric monogram graphic'},

  {slug:'performance-03',   line:'performance', name:'Performance 03 — Blocks',
   desc:'Bauhaus court geometry. The most design-forward piece in the range.',
   tag:'Deep Teal · Performance Poly',
   alt:'Dink Club Performance 03 teal tee — Bauhaus-style geometric block composition'},

  {slug:'performance-04',   line:'performance', name:'Performance 04 — Impact',
   desc:'The moment of contact, blown apart. Loudest shirt we make.',
   tag:'Red · Performance Poly',
   alt:'Dink Club Performance 04 red tee — explosive shard graphic around the DC monogram'},

  {slug:'ducking-finks-heatwave',line:'mascot', name:'Ducking Finks — Miami Heatwave',
   desc:'Sunset, palms, and a duck who knows exactly how good he is.',
   tag:'Black · Unisex Tee',
   alt:'Ducking Finks Miami Heatwave black tee — duck mascot in sunglasses against a palm-tree sunset'},

  {slug:'ducking-finks-rally-riot',line:'mascot',name:'Ducking Finks — Rally Riot',
   desc:'Punk-poster energy on a washed maroon body. Custom inside neck label.',
   tag:'Washed Maroon · Unisex Tee',
   alt:'Ducking Finks Rally Riot maroon washed tee — punk duck mascot in a denim vest holding a paddle'},

  {slug:'ducking-finks-court-chaos',line:'mascot',name:'Ducking Finks — Court Chaos',
   desc:'Night match under the lights, mid-dig, fully committed. The biggest print we make.',
   tag:'Black · Unisex Tee',
   alt:'Ducking Finks Court Chaos black tee — duck mascot lunging for a dig on a floodlit night court'},
];
