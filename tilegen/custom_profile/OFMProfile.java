import com.onthegomap.planetiler.config.Arguments;
import com.onthegomap.planetiler.reader.SourceFeature;
import com.onthegomap.planetiler.reader.WithTags;
import com.onthegomap.planetiler.FeatureCollector;
import com.onthegomap.planetiler.Planetiler;
import com.onthegomap.planetiler.FeatureCollector.Feature;
import java.nio.file.Path;
import org.openmaptiles.OpenMapTilesProfile;
import com.onthegomap.planetiler.util.Translations;
import com.onthegomap.planetiler.config.PlanetilerConfig;
import com.onthegomap.planetiler.stats.Stats;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import com.onthegomap.planetiler.reader.osm.OsmRelationInfo;
import com.onthegomap.planetiler.reader.osm.OsmElement.Relation;

public class OFMProfile extends OpenMapTilesProfile {
    private final List<ICustomizedFeature> customFeatures = List.of(
        new FeatureExtender(
            "transportation",
            List.of(new HasTagsFilter("highway")),
            List.of(new InheritTagsMap("sac_scale", "trail_visibility", "assisted_trail", "via_ferrata_scale", "bicycle", "horse", "level"))
        ),

        new FeatureOverwrite(
            "transportation", 
            TargetGeometry.LINE, 
            List.of(new HasTagsFilter("highway"),new TagValueFilter("highway", "via_ferrata")),
            List.of(
                new TagRemap("highway", "class"),
                new InheritTagsMap("via_ferrata_scale", "sac_scale"),
                new OMTNameMap()
            )
        ),

        // include railways in zoom level 6 and up
        new FeatureExtender(
            "transportation",
            6,
            14,
            List.of(
                new HasTagsFilter("railway")
            ),
            List.of()
        ),

        new FeatureOverwrite(
                "outdoor_route", // Target layer
                TargetGeometry.LINE,
                List.of(
                    new HasTagsFilter("highway"), // Only process if it's a physical highway/trail
                    new RelationsFilter(List.of(   // AND it belongs to a hiking route relation
                        new TagValueFilter("type", "route"),
                        new TagValueFilter("route", "hiking")
                    ))
                ),
                List.of(
                    new RelationTagMap(
                        List.of(
                            new TagValueFilter("type", "route"),
                            new TagValueFilter("route", "hiking")
                        ),
                        // NOTE: add tags used in processor as hint to the preprocessor
                        Set.of("name", "ref", "network", "symbol", "color"),
                        (matchedRelations, vectorFeature) -> {
                            // Your exact sorting and attribute building lambda goes here seamlessly!
                            Map<String, Integer> hikingPriority = Map.of("iwn", 1, "nwn", 2, "rwn", 3, "lwn", 4);
                            var sorted = matchedRelations.stream()
                                .sorted((r1, r2) -> Integer.compare(
                                    hikingPriority.getOrDefault(String.valueOf(r1.getTag("network")), 99), 
                                    hikingPriority.getOrDefault(String.valueOf(r2.getTag("network")), 99)
                                )).toList();

                            int i = 1;
                            for (var rel : sorted) {
                                for (String key : List.of("name", "ref", "network", "symbol", "color")) {
                                    if (rel.hasTag(key)) {
                                        vectorFeature.setAttr("route_" + i + "_" + key, rel.getTag(key));
                                    }
                                }
                                i++;
                            }
                        }
                    )
                )
            )
        );

    @Override
    public void processFeature(SourceFeature sourceFeature, FeatureCollector features) {
        // 1. Check for explicit Overwrites first to stop processing immediately 
        //    if you want to completely override OpenMapTiles base behavior.
        boolean hasCustomOverwrite = false;
        for (ICustomizedFeature customFeature : customFeatures) {
            if (customFeature instanceof FeatureOverwrite && customFeature.filtersMatch(sourceFeature)) {
                customFeature.apply(sourceFeature, features);
                hasCustomOverwrite = true;
            }
        }

        // 2. If no direct Overwrite swallowed the feature, let OMT process it natively.
        // This fills the 'features' collector with default zoom 8 railways and standard highways.
        if (!hasCustomOverwrite) {
            super.processFeature(sourceFeature, features);
        }

        // 3. Extenders MUST run AFTER super.processFeature so they can mutate 
        // the features Planetiler just generated!
        for (ICustomizedFeature customFeature : customFeatures) {
            if (customFeature instanceof FeatureExtender && customFeature.filtersMatch(sourceFeature)) {
                customFeature.apply(sourceFeature, features);
            }
        }
    }
    public enum TargetGeometry { POINT, LINE, POLYGON }

    /**
     *  Interface for a customized feature definition
     *  Defines how to filter source data and how to map it to vector tile attributes.
     */
    public interface ICustomizedFeature{
        /** @return return true if the OSM source matches the requirements for this rule.*/
        public boolean filtersMatch(SourceFeature sourceFeature);
        /** Applies the logic to make a tile feature */
        public void apply(SourceFeature sourceFeature, FeatureCollector features);
        List<Filter> sourceFilters();
        List<TagMapping> tagMappings();

        /** The zoom level at which this feature starts appearing (default 0). */
        default int minZoom() { return 0; }
        /** The zoom level at which this feature stops appearing (defautl 14) */
        default int maxZoom() { return 14; }
    }

    /**
     * Adds additional tags to existing OpenMapTiles features.
     */
    public class FeatureExtender implements ICustomizedFeature {
        private String layer;
        private final List<Filter> sourceFilters;
        private final List<TagMapping> tagMappings;
        private Integer minZoom = null;
        private Integer maxZoom = null;
        
        /**
         * @param layer The destination layer name in the .mbtiles.
         * @param sourceFilters Filters used to catch the OSM feature.
         * @param tagMappings Mappings to define the attributes of the new feature.
         */
        public FeatureExtender(String layer, Integer minZoom, Integer maxZoom, List<Filter> sourceFilters, List<TagMapping> tagMappings) {
            this.layer = layer;
            this.sourceFilters = sourceFilters;
            this.tagMappings = tagMappings;
            this.minZoom = minZoom;
            this.maxZoom = maxZoom;
        }

        /**
         * @param layer The destination layer name in the .mbtiles.
         * @param sourceFilters Filters used to catch the OSM feature.
         * @param tagMappings Mappings to define the attributes of the new feature.
         */
        public FeatureExtender(String layer, List<Filter> sourceFilters, List<TagMapping> tagMappings) {
            this.layer = layer;
            this.sourceFilters = sourceFilters;
            this.tagMappings = tagMappings;
        }

        @Override
        public boolean filtersMatch(SourceFeature sourceFeature) {
            for (int i = 0; i< sourceFilters.size(); i++) {
                if (!sourceFilters.get(i).matches(sourceFeature)) {
                    return false;
                }
            }
            return true;
        }
        @Override
        public void apply(SourceFeature sourceFeature, FeatureCollector features) {
            // OFMProfile
            //.super.processFeature(sourceFeature, features);

            for (var feature : features) {
                if (layer.equals(feature.getLayer())) {
                    if (this.minZoom != null) feature.setMinZoom(this.minZoom);
                    if (this.maxZoom != null) feature.setMaxZoom(this.maxZoom);
                    for (int i = 0; i < tagMappings.size(); i++) {
                        tagMappings.get(i).apply(sourceFeature, feature, DEFAULT_FEATURE_WRITER);
                    }
                }
            }
        }

        public String layer() { return layer; }
        public List<Filter> sourceFilters() { return sourceFilters; }
        public List<TagMapping> tagMappings() { return tagMappings; }
    }

    public class FeatureOverwrite implements ICustomizedFeature {
        // the target layer in which the line will be placed
        private String layer;
        private TargetGeometry targetGeometry;
        private int minZoom;
        private int maxZoom;
        // tags that need to match in order for the feature to be processed
        private List<Filter> sourceFilters;
        private List<TagMapping> tagMappings;
        // tags that will be included directly in the feature.
        private Set<String> includeTags;
        
/**
         * @param layer The destination layer name in the .mbtiles.
         * @param targetGeometry Point, Line, or Polygon.
         * @param minZoom Minimum zoom for the feature.
         * @param maxZoom Maximum zoom for the feature.
         * @param sourceFilters Filters used to catch the OSM feature.
         * @param tagMappings Mappings to define the attributes of the new feature.
         */
        public FeatureOverwrite(
            String layer, 
            TargetGeometry targetGeometry, 
            int minZoom,
            int maxZoom,
            List<Filter> sourceFilters, 
            List<TagMapping> tagMappings
        ) {
            this.layer = layer;
            this.targetGeometry = targetGeometry;
            this.minZoom = minZoom;
            this.maxZoom = maxZoom;
            this.sourceFilters = sourceFilters;
            this.tagMappings = tagMappings;
        }

        /**
         * @param layer The destination layer name in the .mbtiles.
         * @param targetGeometry Point, Line, or Polygon.
         * @param sourceFilters Filters used to catch the OSM feature.
         * @param tagMappings Mappings to define the attributes of the new feature.
         */
        public FeatureOverwrite(String layer, TargetGeometry targetGeometry, List<Filter> sourceFilters, List<TagMapping> tagMappings) {
            this(layer, targetGeometry, 0, 14, sourceFilters, tagMappings);
        }

        @Override public int minZoom() { return minZoom; }
        @Override public int maxZoom() { return maxZoom; }

        @Override
        public boolean filtersMatch(SourceFeature sourceFeature) {
            if (!targetGeometryIsValid(sourceFeature)) return false;
            for (int i = 0; i< sourceFilters.size(); i++) {
                if (!sourceFilters.get(i).matches(sourceFeature)) {
                    return false;
                }
            }
            return true;
        }

        private boolean targetGeometryIsValid(SourceFeature sourceFeature) {
            switch (targetGeometry) {
                case LINE:
                    return sourceFeature.canBeLine();
                case POLYGON:
                    return sourceFeature.canBePolygon();
                case POINT:
                    return sourceFeature.isPoint();
                default:
                    return false;
            }
        }

        @Override
        public void apply(SourceFeature sourceFeature, FeatureCollector features) {
            Feature feature;
            switch(targetGeometry) {
                case LINE:
                    feature = features.line(layer); 
                    break;
                case POLYGON:
                    feature = features.polygon(layer);
                    break;
                case POINT:
                    feature = features.point(layer);
                    break;
                default:
                    // If this happens target gemotries probably should be expanded.
                    return;
            }

            for (var tagMap : tagMappings) {
                tagMap.apply(sourceFeature, feature, DEFAULT_FEATURE_WRITER);
            }
        }

        public String layer() { return this.layer; }
        public TargetGeometry targetGeometry() { return targetGeometry; }
        public List<Filter> sourceFilters() { return sourceFilters; }
        public List<TagMapping> tagMappings() { return tagMappings; }
        public Set<String> includeTags() { return includeTags; }
    }

    @FunctionalInterface
    public interface RelationProcessor extends java.util.function.BiConsumer<List<CustomRelationInfo>, Feature> {}
    
    private static final FeatureWriter DEFAULT_FEATURE_WRITER = (f, key, val, isInherit) -> {
        if (isInherit) {
            f.inheritAttrFromSource(key);
        } else {
            f.setAttr(key, val);
        }
    };

    /**
     * Base interface for all declarative conditional logic.
     * Determines if an object mateches a set of criteria.
     */
    public interface Filter {
        /**
         * Evaluates whether the given element matches the filter's criteria.
         * 
         * @param item The source feature or relation holding tags to evaluate.
         * @return true if the item matches the criteria, false otherwise.
         */
        public boolean matches(WithTags item);
        
        /**
         * Returns the set of OpenStreetMap tag keys that this filter relies on.
         * This allows the configuration to dynamically request required keys during preprocessing.
         * 
         * @return A set of string keys required by the filter.
         */
        public Set<String> getRequiredKeys();
    }
    
    /**
     * A filter that checks if a specific tag key matches one of many allowed values.
     * 
     * @param tagKey The OSM tag key to check (e.g., "highway", "amenity").
     * @param allowedValues The set of values that satisfy this filter.
     */
    public static record TagValueFilter(String tagKey, Set<String> allowedValues) implements Filter {
        /**
         * @param tagKey The OSM tag key to check.
         * @param values A varargs list of values that satisfy this filter.
         */
        public TagValueFilter(String tagKey, String... values) {
            this(tagKey, Set.of(values));
        }

        public boolean matches(WithTags item) {
            if (item == null) return false;

            var featureValue = item.getTag(tagKey);
            return featureValue != null && allowedValues.contains(featureValue);
        }

        public Set<String> getRequiredKeys() {
            return Set.of(tagKey);
        }
    }

    /**
     * An inverted filter that passes only if a specific tag key does NOT match any of the disallowed values.
     * Note: The tag key MUST exist on the feature, but its value must not be in the disallowed set.
     * 
     * @param tagKey The OSM tag key to inspect.
     * @param disallowedValues The set of values that will cause this filter to fail.
     */
    public static record InverseTagValueFilter(String tagKey, Set<Object> disallowedValues) implements Filter {
        /**
         * @param tagKey The OSM tag key to inspect.
         * @param values A varargs list of values that will cause this filter to fail.
         */
        public InverseTagValueFilter(String tagKey, Object... values) {
            this(tagKey, Set.of(values));
        }

        public boolean matches(WithTags item) {
            if (item == null || item.hasTag(tagKey)) return false;

            var featureValue = item.getTag(tagKey);
            return featureValue != null && !disallowedValues.contains(featureValue);
        }

        public Set<String> getRequiredKeys() {
            return Set.of(tagKey);
        }
    }

    /**
     * A filter that ensures all specified tag keys are present on the element, regardless of their values.
     * 
     * @param tagKeys The set of keys that must exist on the element.
     */
    public static record HasTagsFilter(Set<String> tagKeys) implements Filter {
        /**
         * @param tagKeys A varargs list of keys that must exist on the element.
         */
        public HasTagsFilter(String... tagKeys) {
            this(Set.of(tagKeys));
        }
        public boolean matches(WithTags item) {
            return tagKeys.stream().allMatch(key -> item.hasTag(key));
        } 

        public Set<String> getRequiredKeys() {
            return tagKeys;
        }
    }

    /**
     * A relational filter that evaluates the parent OpenStreetMap Relations of a given SourceFeature.
     * This will match any physical feature (like a way) that belongs to a hiking route relation.
     * 
     * @param relationFilters A list of inner filters that must all pass for a single relation.
     */
    public static record RelationsFilter(List<Filter> relationFilters) implements Filter {
        /**
         * @param relationsFilters A varargs list of filters that must all match against a relation.
         */
        public RelationsFilter(Filter... relationsFilters) {
            this(List.of(relationsFilters));
        }

        @Override
        public boolean matches(WithTags item) {
            if (item instanceof SourceFeature sourceFeature) {
                var relationMembers = sourceFeature.relationInfo(CustomRelationInfo.class);
                if (relationMembers == null || relationMembers.isEmpty()) return false;

                for (int i = 0; i < relationMembers.size(); i++) {
                    var member = relationMembers.get(i);
                    if (member.relation() instanceof CustomRelationInfo customRel) {
                        // Match against all inner filters
                        boolean allMatch = true;
                        for (int j = 0; j< relationFilters.size(); j++) {
                            if (!relationFilters.get(j).matches(customRel)) {
                                allMatch = false;
                                break;
                            }
                        }
                        if (allMatch) return true;
                    }
                }
            }
            return false;
        }

        @Override
        public Set<String> getRequiredKeys() {
            // This should only run once so stream should not have a noticable impact on the garbage collector
            return relationFilters.stream()
                .flatMap(f -> f.getRequiredKeys().stream())
                .collect(Collectors.toSet());
        }
    }


    public interface TagMapping {
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer);

        default Set<String> getRequiredKeys() {
            return Collections.emptySet();
        }
    }

    @FunctionalInterface
    public interface FeatureWriter {
        void accept(Feature feature, String key, Object value, boolean isInherit);

        // Convient default method for standard non inherriting attributes
        default void accept(Feature feature, String key, Object value) {
            accept(feature, key, value, false);
        }
    }

    /**
     * Sets a tag under a new key
     */
    public static record TagRemap(String osmTag, String tileTag) implements TagMapping {
        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (sourceFeature == null || feature == null || !sourceFeature.hasTag(osmTag)) return;

            writer.accept(feature, tileTag, sourceFeature.getTag(osmTag));
        }
    }

    /**
     * Add tag with preconfigured value
     */
    public static record TagForceValueMap(String tagKey, Object value) implements TagMapping {

        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (sourceFeature == null || feature == null) return;
            
            writer.accept(feature, tagKey, value);
        }
    }

    /**
     * Apply tagmap if filter is matched
     */
    public static record TagFilterMap(Filter filter, TagMapping map) implements TagMapping {
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (!filter.matches(sourceFeature)) return;
            
            map.apply(sourceFeature, feature, writer);
        }
    }

    /**
     * Applies a set ot tagmaps if all filters are matched.
     */
    public static record TagFiltersMaps(Set<Filter> filters, Set<TagMapping> maps) implements TagMapping {
        /**
         * @param relationFilters Filters to select specific relations (e.g. route=hiking).
         * @param processorTags The keys to extract from the relation in the pre-processing phase.
         * @param processor A lambda to define how relation tags are written to the feature attributes.
         */


        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (!filters.stream().allMatch(filter -> filter.matches(sourceFeature))) return;
            
            maps.forEach(map -> map.apply(sourceFeature, feature, writer));
        }
    }

    /**
     * Inherits available tags from OSM source
     */
    public static record InheritTagsMap(Set<String> tagKeys) implements TagMapping{
        public InheritTagsMap(String... keys) {
            this(Set.of(keys));
        }

        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (sourceFeature == null || feature == null) return;

            for (String tag : tagKeys) {
                if (sourceFeature.hasTag(tag)) {
                    writer.accept(feature, tag, null, true);
                }
            }
        }

        @Override
        public Set<String> getRequiredKeys() {
            return tagKeys;
        }
    }

    /**
     * Inherits tags from the OSM source if the key starts with a specific prefix.
     * Useful for capturing all localized variations like "name:en", "name:fr", etc.
     */
    public static record PatternInheritTagsMap(String prefix) implements TagMapping {
        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (sourceFeature == null || feature == null) return;

            // Loop through all tags present on the physical OSM feature
            for (String tagKey : sourceFeature.tags().keySet()) {
                if (tagKey.startsWith(prefix)) {
                    // Instruct the writer to inherit this specific matching tag from the source
                    writer.accept(feature, tagKey, null, true);
                }
            }
        }

        @Override
        public Set<String> getRequiredKeys() {
            // Planetiler retains localized name tags by default on features, 
            // so we don't need to explicitly register dynamic keys during preprocessing.
            return Collections.emptySet();
        }
    }

    /**
     * Maps name tags to match the official OpenMapTiles schema (name, name_en, name_de, name_int)
     * using the base profile's native translation and name handling utilities.
     */
    public static record OMTNameMap() implements TagMapping {
        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            if (sourceFeature == null || feature == null) return;

            // OpenMapTilesProfile includes built-in OMT name parsing logic.
            // This natively extracts name, name_en, name_de, name_int, and any other target languages.
            for (var entry : org.openmaptiles.util.OmtLanguageUtils.getNamesWithoutTranslations(sourceFeature.tags()).entrySet()) {
                writer.accept(feature, entry.getKey(), entry.getValue());
            }
        }

        @Override
        public Set<String> getRequiredKeys() {
            // Planetiler keeps name and localized variant tags by default on features.
            return Collections.emptySet();
        }
    }

    /**
     * Set a zoom restriction for a specific tagMap.
     */
    public static record ZoomRestrictedTagMap(int minZoom, TagMapping nestedMapping) implements TagMapping {
        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, OFMProfile
    .FeatureWriter writer) {
            nestedMapping.apply(sourceFeature, feature, this::writeZoomRestricted);
        }

        private void writeZoomRestricted(Feature f, String key, Object val, boolean isInherit) {
            if (isInherit) {
                f.inheritAttrsFromSourceWithMinzoom(minZoom, key);
            } else {
                f.setAttrWithMinzoom(key, val, minZoom);
            }
        }

        @Override
        public Set<String> getRequiredKeys() {
            return nestedMapping.getRequiredKeys();
        }
    }

    /**
     * Add tags that come from a relation member
     */
    public static record RelationTagMap(
        List<Filter> relationFilters,
        Set<String> processorTags, // NOTE: add tags used in the lambda processor
        RelationProcessor processor
    ) implements TagMapping{

        @Override
        public void apply(SourceFeature sourceFeature, Feature feature, FeatureWriter writer) {
            var relationMembers = sourceFeature.relationInfo(CustomRelationInfo.class);
            if (relationMembers == null || relationMembers.isEmpty()) return;

            List<CustomRelationInfo> matchedRelations = new ArrayList<>(relationMembers.size());

            for (int i = 0; i < relationMembers.size(); i++) {
                var member = relationMembers.get(i);
                if (member.relation() instanceof CustomRelationInfo customRel) {
                    boolean matchesAll = true;
                    for (int j = 0; j < relationFilters.size(); j++) {
                        if (!relationFilters.get(j).matches(customRel)) {
                            matchesAll = false;
                            break;
                        }
                    }
                    if (matchesAll) {
                        matchedRelations.add(customRel);
                    }
                }
            }
            if (!matchedRelations.isEmpty()) {
                processor.accept(matchedRelations, feature);
            }
        }

        @Override
        public Set<String> getRequiredKeys() {
            Set<String> keys = new HashSet<>(processorTags);
            for (Filter filter : relationFilters) {
                keys.addAll(filter.getRequiredKeys());
            }
            return keys;
        }
    }

    private record CustomRelationInfo(
        long id,
        Map<String, Object> tags
    ) implements OsmRelationInfo, WithTags {
        @Override
        public long id() { return id; }

        public Object getTag(String key) {
            return tags.get(key);
        }

        public boolean hasTag(String key) {
            return tags.containsKey(key);
        }
    }

    private static class RelationPreprocessorRuleset {
        record RuleMatcher(List<Filter> relationFilters, Set<String> requiredKeys) {}

        private final List<RuleMatcher> matchers = new ArrayList<>();

        public RelationPreprocessorRuleset(List<ICustomizedFeature> customFeatures) {
            for (int i = 0; i< customFeatures.size(); i++) {
                ICustomizedFeature rule = customFeatures.get(i);
                List<Filter> filters = rule.sourceFilters();

                for (int j = 0; j < filters.size(); j++) {
                    if (filters.get(j) instanceof RelationsFilter relationFilter) {
                        // Gather all keys required by this filter and the rule's tag mapping
                        Set<String> keys = new HashSet<>(relationFilter.getRequiredKeys());
                        List<TagMapping> mappings = rule.tagMappings();
                        for (int m = 0; m < mappings.size(); m++) {
                            keys.addAll(mappings.get(m).getRequiredKeys());
                        }

                        matchers.add(new RuleMatcher(
                            relationFilter.relationFilters(), 
                            Collections.unmodifiableSet(keys)
                        ));
                    }
                }
            }
        }

        public List<RuleMatcher> matchers() {
            return matchers;
        }
    }

    @Override
    public List<OsmRelationInfo> preprocessOsmRelation(Relation relation) {
        if (relation == null) return null;
        Set<String> dynamicRequiredKeys = null;
        List<RelationPreprocessorRuleset.RuleMatcher> matchers = relationRuleset.matchers();

        for (int i = 0; i < matchers.size(); i++) {
            var matcher = matchers.get(i);
            List<Filter> innerFilters = matcher.relationFilters();

            boolean relationMatches = true;
            for (int j = 0; j < innerFilters.size(); j++) {
                if (!innerFilters.get(j).matches(relation)) {
                    relationMatches = false;
                    break;
                }
            }

            // If the relation matches the rule, merge pre-computed keys
            if (relationMatches) {
                if (dynamicRequiredKeys == null) {
                    dynamicRequiredKeys = new HashSet<>();
                }
                dynamicRequiredKeys.addAll(matcher.requiredKeys());
            }
        }

        // Build minimal tag map for found keys
        if (dynamicRequiredKeys != null && !dynamicRequiredKeys.isEmpty()) {
            Map<String, Object> minimalTags = new HashMap<>(dynamicRequiredKeys.size());

            for (String tagKey : dynamicRequiredKeys) {
                if (relation.hasTag(tagKey)) {
                    minimalTags.put(tagKey, relation.getTag(tagKey));
                }
            }

            if (minimalTags.isEmpty()) return null;

            List<OsmRelationInfo> matched = new ArrayList<>(1);
            matched.add(new CustomRelationInfo(relation.id(), minimalTags));
            return matched;
        }
        return null;
    }

    private final RelationPreprocessorRuleset relationRuleset;

    public OFMProfile
(Planetiler runner) {
        super(runner.translations(), runner.config(), runner.stats());
        this.relationRuleset = new RelationPreprocessorRuleset(this.customFeatures);
    }

    public OFMProfile
(Translations translations, PlanetilerConfig config, Stats stats) {
        super(translations,config,stats);
        this.relationRuleset = new RelationPreprocessorRuleset(this.customFeatures);
    }

    public static void main(String[] args) {
        // arguments CLI avec download par défaut
        var arguments = Arguments.fromArgs(args).withDefault("download", true);

        // initialize Planetiler
        Planetiler runner = Planetiler.create(arguments);

        // Set custom profile
        var profile = new OFMProfile
    (runner);

        // execute
        runner.setProfile(profile)
              .addOsmSource("osm", Path.of("data", "monaco-latest.osm.pbf"), "geofabrik:monaco")
              .overwriteOutput(Path.of("data", "custom.mbtiles"))
              .run();
    }
}