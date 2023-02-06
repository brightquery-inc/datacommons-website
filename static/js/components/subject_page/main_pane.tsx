/**
 * Copyright 2021 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Component for rendering the main pane of a subject page.
 */

import _ from "lodash";
import React, { memo, useEffect, useState } from "react";

import { SVG_CHART_HEIGHT } from "../../constants/tile_constants";
import { NamedPlace, NamedTypedPlace } from "../../shared/types";
import { SubjectPageConfig } from "../../types/subject_page_proto_types";
import { fetchGeoJsonData } from "../../utils/subject_page_utils";
import { ErrorBoundary } from "../error_boundary";
import { Category } from "./category";
import { DataContext } from "./data_context";

interface SubjectPageMainPanePropType {
  // The place to show the page for.
  place: NamedTypedPlace;
  // Config of the page
  pageConfig: SubjectPageConfig;
  // Height, in px, for the tile SVG charts.
  svgChartHeight?: number;
  // parent places of the place to show the page for.
  parentPlaces?: NamedPlace[];
}

export const SubjectPageMainPane = memo(function SubjectPageMainPane(
  props: SubjectPageMainPanePropType
): JSX.Element {
  // TODO(shifucun): Further clean up default place type, child place type etc
  // from subject page client components. The component should respect whatever
  // the input prop is.
  let enclosedPlaceType = "";
  for (const placeType of props.place.types) {
    if (
      props.pageConfig.metadata.containedPlaceTypes &&
      placeType in props.pageConfig.metadata.containedPlaceTypes
    ) {
      enclosedPlaceType =
        props.pageConfig.metadata.containedPlaceTypes[placeType];
    }
  }
  const [geoJsonData, setGeoJsonData] = useState(null);

  useEffect(() => {
    // re-fetch geojson data if props change
    fetchGeoJsonData(props.place, enclosedPlaceType, props.parentPlaces).then(
      (geoJsonData) => {
        setGeoJsonData(geoJsonData);
      }
    );
  }, [props]);

  return (
    <div id="subject-page-main-pane">
      {!_.isEmpty(props.pageConfig) &&
        props.pageConfig.categories.map((category, idx) => {
          const id = `cat${idx}`;
          return (
            <DataContext.Provider key={id} value={{ geoJsonData }}>
              <ErrorBoundary>
                <Category
                  id={id}
                  place={props.place}
                  enclosedPlaceType={enclosedPlaceType}
                  config={category}
                  eventTypeSpec={props.pageConfig.metadata.eventTypeSpec}
                  svgChartHeight={
                    // TODO: Unroll this for NL and use container offset from CSS instead.
                    props.svgChartHeight
                      ? props.svgChartHeight
                      : SVG_CHART_HEIGHT
                  }
                />
              </ErrorBoundary>
            </DataContext.Provider>
          );
        })}
    </div>
  );
});
