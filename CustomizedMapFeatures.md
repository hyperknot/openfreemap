# Customized Map Features #
This documment is intendet to provide an introduction to altering map profiles.
This system is the result of trying to have a somewhat declarative method of customizing a map without the limitations of the default yaml customisations.

The OFMProfile is located in OFMProfile.java

The __customFeatures__ list is used to declare custom features for the map pofile.  
A custom feature may either overwrite the original map logic completely, or extend to a default feature.  

A basic feature will require a couple of things:
1. A target layer: this defines in which layer of the final mbtiles this feature will be placed.
2. A target Geometry: May be rendered as Polygon/Line/Point
3. A list of conditions that must be matched in order to be processed using this FeatureOverwrite
4. A list of tags that will be exported to this Feature in the final tile.

Lets say we want to add via ferratas to the transportation layer we can define the following:
```java
private final List<ICustomizedFeature> customFeatures = List.of(
    new FeatureOverwrite(
        // Place the feature in the transportation layer.
        "transportation", 
        // The feature MUST be able to be rendered as a line
        TargetGeometry.LINE, 
        // The following filters must be matched on the input data
        List.of(new HasTagsFilter("highway"),new TagValueFilter("highway", "via_ferrata")),
        // The following tags are to be exported onto the final feature
        List.of(
            new TagRemap("highway", "class"),
            new InheritTagsMap("via_ferrata_scale", "sac_scale"),
            new OMTNameMap()
        )
    )
);
```
If the input data can be rendered as a Line, has the tag highway, and the highway tag has the value of via_ferrata this feature will be added to the transportation layer using only our custom feature, the default logic to process this data will not be executed.  

If you wish to add a certain tag to a default mapfeature you can define an extention.
```java
    new FeatureExtender(
        "transportation",
        List.of(new HasTagsFilter("highway")),
        List.of(new InheritTagsMap("sac_scale", "trail_visibility", "assisted_trail", "via_ferrata_scale", "bicycle", "horse", "level"))
    )
```
This extention will try to match its filters on any feature that the default logic has placed in the transportation layer.  
When such a feature has the highway tag an attempt will be made to add each of the tags in the final list.

## Filters ##
Filters provide us the ability to create conditions under which our custom logic will be executed.
* __TagValueFillter__: Evaluate if the specified tags value matches one of the provided values.
* __InverseTagValueFilter__: Inverse of the TagValueFilter, a tags value may not match any of the provided values.
* __HasTagsFilter__: Evaluete if the specified tag is pressent
* __RelationsFilter__: Evaluate OSM relations of the OSM feature.

## Mapping tags onto features ##
Order to add tags to our features we can provide tagmaps. These provide a way to customize how information is coppied from the OSM source onto the final feature.
* __InheritTagsMap__: This copies the specified tag and its value directly from the OSM source.
* __TagRemap__: Provides a way to change the name of a tag without altering the value of the tag
* __TagForceValueMap__: Add a tag certain tag with a predetermined value.
* __TagFilterMap__: Takes a single filter and a single tagmapping, this only applies the tag map if the conditions of the provided filter is matched.
* __TagFiltersMaps__: Takes a list of filters and a list of tagmappings, and only applies the tag maps if all of the filters are matched.
* __PatternInheritTagsMap__: If the start of a tag (the key not the inner value) matches the provided value the tag will be inherited. This can be used for localized variations like name:xx
* __OMTNameMap__: This provides a way to add the default OpenMapTiles nameing scheme onto a feature by suppling name, name_en, name_de, and name_int.
* __ZoomRestrictedTagMap__: This provides a way to overwrite the zoom levels at which a specified tag will be added to a feature.

## Adding Relation tags ##
Finally there is the existance of relations.  
Lets say we are processing a path which is part of one or more hiking routes, when processing a piece of the path these routes are accessable through relations.
To get tags from a relation to a feature they need to be provided through a preprocessor.  
The __relationTagMap__ provides a set of filters, a set of tags, and a "Relation Processor", to the preprocessing step.

The filters are used to build the conditioning of wether or not to extract tags from a relations just like they are used for wether or not to process a feature.  
The set of tags are used to tell the preprocessor those keys are required when processing a feature for which this relation matches the condition created by the filters. Tags used by the filters are added automatically in the preprocessing step.  

The RelationProcessor provides a way of customizing tags in the preprocessor.  
Currently there is no default implementation that can be provided.
When a specific behaviour is required in more than one custom feature you may want to define this behaviour in a system like: 
```java
public static final RelationProcessor custombehaviour = (matchedRelations, vectorFeature) -> { /* Define your custom behaviour here. */ };
```
If custom behaviour is only required once you can just provide the RelationProcessor via a lambda function.
Take for example this feature overwrite that creates a feature in an outdoor_route layer for hiking routes.  
```java
new FeatureOverwrite(
    "outdoor_route", // Target layer
    TargetGeometry.LINE,
    List.of(
        new HasTagsFilter("highway"), // Only process physical highways/trails
        new RelationsFilter(List.of(   // AND belongs to a hiking route relation
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
            // Explicitly pass required keys for pre-processing retention
            Set.of("name", "ref", "network", "symbol", "color"),
            // Lambda implementation
            (matchedRelations, vectorFeature) -> {
                Map<String, Integer> hikingPriority = Map.of("iwn", 1, "nwn", 2, "rwn", 3, "lwn", 4);
                
                // Sort relations by network hierarchy priority
                var sorted = matchedRelations.stream()
                    .sorted((r1, r2) -> Integer.compare(
                        hikingPriority.getOrDefault(String.valueOf(r1.getTag("network")), 99), 
                        hikingPriority.getOrDefault(String.valueOf(r2.getTag("network")), 99)
                    )).toList();

                // Dynamically build and assign indexed attributes
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
```
During the preprocessing step the filters are used to check if relations match the required conditions, after which the preprocessor will provide the relavant tags to to the RelationProcessor.  
The relation processor is used to then apply the tags provided by the preprocessor onto the final feature.  
In this axample we sort the provided relations based on a key, before adding each of the name, ref, network, symbol, and color tags for each route to the final feature.